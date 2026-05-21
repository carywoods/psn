import cobra
import os
import datetime
import json
from dotenv import load_dotenv

# Import PSN Modules
from sim_engine.grr1_sensor_module import apply_grr1_sensor
from sim_engine.goebl_regulatory_layer import apply_goebl_tax, calculate_regulatory_burden

# Load environment variables
load_dotenv()

def run_fba_simulation(scenario="PURINE_BOTTLENECK"):
    """
    Standard FBA Simulation Runner for PSN.
    """
    model_path = "sim_engine/yeast9.xml"
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found.")
        return
    
    print(f"Loading model: {model_path}...")
    model = cobra.io.read_sbml_model(model_path)
    model.solver.configuration.processes = 20
    
    if scenario == "PURINE_BOTTLENECK":
        print("Scenario: Simulating Purine Bottleneck (GL 1000109)...")
        # Target reactions for GL 1000109: r_0570, r_0912
        for rid in ['r_0570', 'r_0912']:
            if rid in model.reactions:
                rxn = model.reactions.get_by_id(rid)
                rxn.lower_bound = -0.01
                rxn.upper_bound = 0.01
                print(f"Constraint applied to {rid} ({rxn.name}): bounds set to 0.01")
                
    # Default growth conditions (Aerobic Glucose)
    if 'r_1714' in model.reactions:
        model.reactions.r_1714.lower_bound = -10.0
        
    print("Running 20-threaded Optimization...")
    solution = model.optimize()
    growth_rate = solution.objective_value
    
    print(f"--- {scenario} Results ---")
    print(f"Growth Rate: {growth_rate:.4f}")
    
    log_simulation(growth_rate, scenario)

def log_simulation(growth, scenario):
    log_entry = f"\n\n### GLPath Simulation Run ({scenario}): {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    log_entry += f"- **Scenario:** {scenario}\n"
    log_entry += f"- **Target:** GL 1000109 (IMP Step)\n"
    log_entry += f"- **Growth Rate:** {growth:.6f}\n"
    log_entry += f"- **Hardware Utilization:** 20 threads (i9-12900HK)\n"
    
    with open("GEMINI.md", "a") as f:
        f.write(log_entry)
    print("Logged results to GEMINI.md")

if __name__ == "__main__":
    run_fba_simulation("PURINE_BOTTLENECK")
