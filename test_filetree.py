from utils.zip_handler import flatten_zip_hierarchy

# Test with a zip file
input_zip = 'test_structure.zip'
output_path = flatten_zip_hierarchy(input_zip, output_format='text', delimiter='^^')

print(f"Output file created: {output_path}")
print("\nContent of the output file:")
with open(output_path, 'r', encoding='utf-8') as f:
    print(f.read())