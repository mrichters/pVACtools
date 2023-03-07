import os
import sys
import yaml
import pkg_resources
def status_message(msg):
    print(msg)
    sys.stdout.flush()
class PrintLog:
    def __init__(self, args_input):
        self.args_dict = vars(args_input)
        self.log_dir = os.path.join(self.args_dict['output_dir'], 'log')
        os.makedirs(self.log_dir, exist_ok=True)

    def execute(self):
        log_file = os.path.join(self.log_dir, 'inputs.yml')
        if os.path.exists(log_file):
            with open(log_file, 'r') as log_fh:
                past_inputs = yaml.load(log_fh, Loader=yaml.FullLoader)
                current_inputs = self.args_dict
                current_inputs['pvactools_version'] = pkg_resources.get_distribution("pvactools").version
                current_keys = list(current_inputs.keys())
                current_keys.sort()
                current_inputs = {i: current_inputs[i] for i in current_keys}
                if past_inputs['pvactools_version'] != current_inputs['pvactools_version']:
                    status_message(
                        "Restart to be executed with a different pVACtools version:\n" +
                        "Past version: %s\n" % past_inputs['pvactools_version'] +
                        "Current version: %s" % current_inputs['pvactools_version']
                    )
                for key in current_inputs.keys():
                    if key == 'pvactools_version' or key == 'pvacseq_version':
                        continue
                    if key not in past_inputs.keys() and current_inputs[key] is not None:
                        print(current_inputs[key])
                        print(past_inputs[key])
                        sys.exit(
                            "Restart inputs are different from past inputs: \n" +
                            "Additional input: %s - %s\n" % (key, current_inputs[key]) +
                            "Aborting."
                        )
                    elif current_inputs[key] != past_inputs[key]:
                        print(current_inputs[key])
                        print(past_inputs[key])
                        sys.exit(
                            "Restart inputs are different from past inputs: \n" +
                            "Past input: %s - %s\n" % (key, past_inputs[key]) +
                            "Current input: %s - %s\n" % (key, current_inputs[key]) +
                            "Aborting."
                        )
        else:
            with open(log_file, 'w') as log_fh:
                inputs = self.args_dict
                inputs['pvactools_version'] = pkg_resources.get_distribution("pvactools").version
                yaml.dump(inputs, log_fh, default_flow_style=False)
