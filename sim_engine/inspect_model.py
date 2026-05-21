import cobra
import sys

def inspect_model(model_path):
    try:
        model = cobra.io.read_sbml_model(model_path)
        print(f"Model: {model.id}")
        print(f"Objective: {model.objective}")
        # Identify exchange reactions
        glucose = model.reactions.get_by_id("r_1714")
        oxygen = model.reactions.get_by_id("r_1992")
        ethanol = model.reactions.get_by_id("r_1761")
        print(f"Glucose: {glucose.name} ({glucose.id})")
        print(f"Oxygen: {oxygen.name} ({oxygen.id})")
        print(f"Ethanol: {ethanol.name} ({ethanol.id})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_model("sim_engine/yeast9.xml")
