def calculate_focus(Z):
    """Calculate focus value for a given zoom value using a 5th-degree polynomial."""
    try:
        return (4.7105e-10 * Z**5) - (1.7064e-7 * Z**4) + (1.9530e-5 * Z**3) - (2.0363e-3 * Z**2) - (0.5778 * Z) + 240.7969
    except Exception as e:
        print(f"Error calculating focus for Z={Z}: {e}")
        return None

def generate_zoom_focus_values():
    """Generate zoom and focus values in real-time and return as a list of dictionaries."""
    zoom_focus_data = []
    
    # Loop through zoom values from 80 to 243
    for Z in range(80, 244, 1):
        try:
            # Calculate and round the focus value
            focus_value = calculate_focus(Z)
            if focus_value is None:
                continue
            focus_value = round(focus_value)
            zoom_focus_data.append({"Zoom": Z, "Focus": focus_value})
        except Exception as e:
            print(f"Error processing Z={Z}: {e}")
            continue
    
    print(f"Generated {len(zoom_focus_data)} zoom and focus value pairs")
    return zoom_focus_data

def main():
    """Main function to generate and display zoom and focus values."""
    print("Generating zoom and focus values...")
    values = generate_zoom_focus_values()
    for row in values:
        print(f"Zoom: {row['Zoom']}, Focus: {row['Focus']}")

if __name__ == "__main__":
    main()