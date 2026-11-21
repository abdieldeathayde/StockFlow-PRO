from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import ParseError as XMLParseError
from uuid import uuid4
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Product
from app.services import audit

HEADERS = (
    'nome da peça',
    'locação',
    'quantidade',
    'preço unitário',
    'ncm',
)


class ProductImportError(ValueError):
    pass


def _normalized_name(value):
    return ' '.join(value.split()).casefold()


def _parse_decimal(value, row_number, field):
    if value is None or isinstance(value, bool):
        raise ProductImportError(f'Linha {row_number}: informe {field}.')

    text_value = str(value).strip().replace('R$', '').replace(' ', '').replace('\xa0', '')
    if ',' in text_value:
        if '.' in text_value:
            if text_value.rfind(',') > text_value.rfind('.'):
                text_value = text_value.replace('.', '').replace(',', '.')
            else:
                text_value = text_value.replace(',', '')
        else:
            text_value = text_value.replace(',', '.')

    try:
        number = Decimal(text_value)
    except InvalidOperation as error:
        raise ProductImportError(f'Linha {row_number}: valor inválido para {field}.') from error
    if not number.is_finite():
        raise ProductImportError(f'Linha {row_number}: valor inválido para {field}.')
    return number


def _cell_text(cell, pad_ncm=False):
    value = cell.value
    if value is None:
        return ''
    if pad_ncm and isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric_value = Decimal(str(value))
        if numeric_value == numeric_value.to_integral_value():
            return str(int(numeric_value)).zfill(8)
    return str(value).strip()


def import_products_xlsx(organization_id, user_id, file_stream):
    try:
        workbook = load_workbook(file_stream, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError) as error:
        raise ProductImportError('O arquivo não é um .xlsx válido ou está corrompido.') from error

    try:
        worksheet = workbook.active
        rows = worksheet.iter_rows()
        header_cells = next(rows, None)
        if not header_cells:
            raise ProductImportError('A planilha está vazia.')

        header_indexes = {}
        for index, cell in enumerate(header_cells):
            header = ' '.join(str(cell.value or '').split()).casefold()
            if header in HEADERS:
                if header in header_indexes:
                    raise ProductImportError(f'A coluna "{header}" aparece mais de uma vez.')
                header_indexes[header] = index

        missing_headers = [header for header in HEADERS if header not in header_indexes]
        if missing_headers:
            raise ProductImportError(
                'Colunas obrigatórias ausentes: ' + ', '.join(missing_headers) + '.'
            )

        existing_names = {
            _normalized_name(name)
            for (name,) in db.session.query(Product.name).filter_by(
                organization_id=organization_id
            ).all()
        }
        seen_names = set()
        products = []
        skipped_duplicates = 0
        skipped_incomplete = 0
        skipped_invalid = 0

        for row_number, cells in enumerate(rows, start=2):
            if all(cell.value is None or str(cell.value).strip() == '' for cell in cells):
                continue

            def value_for(header):
                index = header_indexes[header]
                return cells[index] if index < len(cells) else None

            name_cell = value_for('nome da peça')
            name = _cell_text(name_cell) if name_cell else ''
            if not name:
                skipped_incomplete += 1
                continue

            normalized_name = _normalized_name(name)
            if normalized_name in existing_names or normalized_name in seen_names:
                skipped_duplicates += 1
                continue

            location_cell = value_for('locação')
            location = _cell_text(location_cell) if location_cell else ''
            ncm_cell = value_for('ncm')
            ncm = _cell_text(ncm_cell, pad_ncm=True) if ncm_cell else ''
            quantity_cell = value_for('quantidade')
            price_cell = value_for('preço unitário')

            if len(name) > 160:
                skipped_invalid += 1
                continue
            if len(location) > 120:
                skipped_invalid += 1
                continue
            if len(ncm) > 20:
                skipped_invalid += 1
                continue
            if quantity_cell is None or quantity_cell.value is None or str(quantity_cell.value).strip() == '':
                skipped_incomplete += 1
                continue
            if price_cell is None or price_cell.value is None or str(price_cell.value).strip() == '':
                skipped_incomplete += 1
                continue

            try:
                quantity = _parse_decimal(quantity_cell.value, row_number, 'quantidade')
            except ProductImportError:
                skipped_invalid += 1
                continue
            if quantity != quantity.to_integral_value() or quantity < 0 or quantity > 2147483647:
                skipped_invalid += 1
                continue

            try:
                unit_price = _parse_decimal(price_cell.value, row_number, 'preço unitário')
            except ProductImportError:
                skipped_invalid += 1
                continue
            if unit_price < 0 or unit_price > Decimal('9999999999.99'):
                skipped_invalid += 1
                continue
            if unit_price.quantize(Decimal('0.01')) != unit_price:
                skipped_invalid += 1
                continue

            seen_names.add(normalized_name)
            products.append(Product(
                organization_id=organization_id,
                sku=f'IMPORT-{uuid4().hex[:12].upper()}',
                name=name,
                location=location,
                ncm=ncm,
                quantity=int(quantity),
                cost_price=unit_price,
                sale_price=Decimal('0.00'),
            ))

        if not products and not skipped_duplicates and not skipped_incomplete and not skipped_invalid:
            raise ProductImportError('A planilha não contém peças para importar.')
        if products:
            db.session.add_all(products)
            try:
                db.session.flush()
                for product in products:
                    audit(
                        organization_id,
                        user_id,
                        'IMPORT',
                        'Product',
                        product.id,
                        product.sku,
                    )
                db.session.commit()
            except IntegrityError as error:
                db.session.rollback()
                raise ProductImportError(
                    'Não foi possível salvar a importação. Nenhum produto foi importado.'
                ) from error

        return len(products), skipped_duplicates, skipped_incomplete, skipped_invalid
    except XMLParseError as error:
        raise ProductImportError('A planilha contém dados XLSX inválidos ou corrompidos.') from error
    finally:
        workbook.close()
