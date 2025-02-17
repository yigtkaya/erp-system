from decimal import Decimal
import re

class MaterialType:
    STEEL = 'STEEL'
    ALUMINUM = 'ALUMINUM'
    
    @staticmethod
    def from_turkish(text):
        mapping = {
            'Çelik': 'STEEL',
            'Alüminyum': 'ALUMINUM'
        }
        return mapping.get(text, 'STEEL')

def parse_dimension(value):
    if not value:
        return None
    # Remove any non-numeric characters except decimal point and convert to float
    clean_value = re.sub(r'[^0-9.]', '', value.replace(',', '.'))
    return float(clean_value) if clean_value else None

def extract_dimensions(stock_name, diameter_mm):
    """Extract width, height, thickness from stock name or diameter"""
    dimensions = {'width': None, 'height': None, 'thickness': None, 'diameter_mm': None}
    
    # Handle diameter first
    if diameter_mm and diameter_mm.strip() not in ['', 'null']:
        # Improved diameter parsing with unit conversion
        if match := re.search(r'[\d.,]+', diameter_mm.replace(',', '.')):
            try:
                dimensions['diameter_mm'] = float(match.group().strip())
            except ValueError:
                pass
        return dimensions

    # Improved dimension pattern matching with multiple separators
    dimension_pattern = r'''
        (\d+[\.,]?\d*)   # Width
        [xX×*]           # Separator
        (\d+[\.,]?\d*)   # Height 
        (?:[xX×*]        # Optional thickness
        (\d+[\.,]?\d*))? # Thickness (optional)
    '''
    
    if match := re.search(dimension_pattern, stock_name, re.VERBOSE):
        dimensions['width'] = parse_dimension(match.group(1))
        dimensions['height'] = parse_dimension(match.group(2))
        if match.group(3):
            dimensions['thickness'] = parse_dimension(match.group(3))
    
    return dimensions

def parse_sql_values(sql_string):
    # Regular expression to match the values in the INSERT statement
    pattern = r"\('([^']*)', '([^']*)', '([^']*)', '([^']*)', '([^']*)', ([^,]*), ([^,]*), ([^,]*), '([^']*)', '([^']*)'\)"
    
    raw_materials = []
    
    for match in re.finditer(pattern, sql_string):
        material_type, stock_code, material, stock_name, diameter_mm, width, height, thickness, stock_amount, unit = match.groups()
        
        # Clean up NULL values
        width = None if width == 'null' else width
        height = None if height == 'null' else height
        thickness = None if thickness == 'null' else thickness
        
        # Extract dimensions
        dimensions = extract_dimensions(stock_name, diameter_mm)
        
        # If explicit dimensions were provided in the SQL, use those instead
        if width and width != 'null':
            dimensions['width'] = parse_dimension(width)
        if height and height != 'null':
            dimensions['height'] = parse_dimension(height)
        if thickness and thickness != 'null':
            dimensions['thickness'] = parse_dimension(thickness)
        
        # Create description string with dimensions
        description_parts = []
        if dimensions['diameter_mm']:
            description_parts.append(f"Diameter: {dimensions['diameter_mm']}mm")
        if dimensions['width']:
            description_parts.append(f"Width: {dimensions['width']}mm")
        if dimensions['height']:
            description_parts.append(f"Height: {dimensions['height']}mm")
        if dimensions['thickness']:
            description_parts.append(f"Thickness: {dimensions['thickness']}mm")
        
        description = f"{material} - {' | '.join(description_parts)}" if description_parts else material
        
        raw_material = {
            'product_code': stock_code,
            'product_name': stock_name,
            'description': description,
            'current_stock': int(float(stock_amount)),
            'material_type': MaterialType.from_turkish(material_type)
        }
        
        raw_materials.append(raw_material)
    
    return raw_materials

# Example usage
sql_input = """[Your SQL INSERT statement here]"""
raw_materials = parse_sql_values(sql_input)

# Print example output
for material in raw_materials[:3]:  # Show first 3 materials
    print("\nRaw Material:")
    for key, value in material.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    # Read the SQL file
    with open('/Users/hasanyigitkaya/Downloads/raw_materials_rows.sql', 'r') as file:
        sql_input = file.read()
    
    # Parse the SQL values
    raw_materials = parse_sql_values(sql_input)
    
    # Print the results in Python list format
    print("raw_materials_data = [")
    for material in raw_materials:
        print("    {")
        for key, value in material.items():
            if isinstance(value, str):
                # Handle multi-line strings and special characters
                safe_value = value.replace("'", "\\'").replace('\n', ' ')
                print(f"        '{key}': '{safe_value}',")
            else:
                print(f"        '{key}': {value},")
        print("    },")
    print("]")