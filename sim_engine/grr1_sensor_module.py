def apply_grr1_sensor(glucose_flux, base_ngam):
    """
    GRR1 Sensor Module: Monitors Glucose Uptake (r_1714).
    - Nutrient Signaling Mode: If |flux| > 5.0, decrease NGAM by 10%.
    - Glucose Repression Release: If |flux| < 0.5, increase Proteolytic Tax by 20%.
    """
    abs_flux = abs(glucose_flux)
    ngam_adjustment = 1.0
    proteolytic_tax = 1.0

    if abs_flux > 5.0:
        # Nutrient Signaling Mode
        ngam_adjustment = 0.90
        mode = "NUTRIENT_SIGNALING"
    elif abs_flux < 0.5:
        # Glucose Repression Release
        proteolytic_tax = 1.20
        mode = "REPRESSION_RELEASE"
    else:
        mode = "NORMAL"

    new_ngam = base_ngam * ngam_adjustment
    return new_ngam, proteolytic_tax, mode

if __name__ == "__main__":
    # Test cases
    print(f"High Glucose (-10): {apply_grr1_sensor(-10, 0.7)}")
    print(f"Low Glucose (-0.2): {apply_grr1_sensor(-0.2, 0.7)}")
