from nipype.interfaces.base import BaseInterfaceInputSpec, TraitedSpec,\
    BaseInterface
from nipype.interfaces.traits_extension import File
import enthought.traits.api as traits

def parse_line_bisection_log(filename, delay):
    file = open(filename)
    for i in range(5):
        file.readline()
    
    pulses = []
    pictures = {"task":[], "rest":[]}
    correct_pictures = {"task":[], "rest":[]}
    incorrect_pictures = {"task":[], "rest":[]}
    noresponse_pictures = {"task":[], "rest":[]}
    block = None
    last_picture_time = None
    for line in file:
        line_split = line.split()
        event = line_split[2]
        type = line_split[3]
        time = float(line_split[4]) / 10000.0 - delay
        if event == "Picture" and type == "task_instruction":
            if last_picture_time:
                noresponse_pictures[block].append(last_picture_time)
                last_picture_time = None
            block = "task"
        elif event == "Picture" and type == "rest_instruction":
            if last_picture_time:
                noresponse_pictures[block].append(last_picture_time)
                last_picture_time = None
            block = "rest"
        elif event == "Pulse":
            pulses.append(time)
        elif event == "Picture" and type in ["incorrect", "correct"]:
            if last_picture_time:
                noresponse_pictures[block].append(last_picture_time)
            pictures[block].append(time)
            last_picture_time = time
        elif last_picture_time and event == "Response":
            if type == "10":
                correct_pictures[block].append(last_picture_time)
            else:
                incorrect_pictures[block].append(last_picture_time)
            last_picture_time = None
    
    if last_picture_time:
        noresponse_pictures[block].append(last_picture_time)
        
    assert len(pictures["task"]) == len(correct_pictures["task"]) + len(incorrect_pictures["task"]) + len(noresponse_pictures["task"])
    assert len(pictures["rest"]) == len(correct_pictures["rest"]) + len(incorrect_pictures["rest"]) + len(noresponse_pictures["rest"])
    
    return pulses, pictures, correct_pictures, incorrect_pictures, noresponse_pictures

class ParseLineBisectionLogInputSpec(BaseInterfaceInputSpec):
    log_file = File(exists=True, mandatory = True)
    delay = traits.Float(0, usedefault=True)
    
class ParseLineBisectionLogOutputSpec(TraitedSpec):
    pulses = traits.List()
    pictures = traits.Dict()
    correct_pictures = traits.Dict()
    incorrect_pictures = traits.Dict()
    noresponse_pictures = traits.Dict()
    
class ParseLineBisection(BaseInterface):
    input_spec = ParseLineBisectionLogInputSpec
    output_spec = ParseLineBisectionLogOutputSpec
    
    def _run_interface(self, runtime):
        
        self._pulses, self._pictures, self._correct_pictures, self._incorrect_pictures, self._noresponse_pictures = parse_line_bisection_log(self.inputs.log_file, self.inputs.delay)
        
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["pulses"] = self._pulses
        outputs["pictures"] = self._pictures
        outputs["correct_pictures"] = self._correct_pictures
        outputs["incorrect_pictures"] = self._incorrect_pictures
        outputs["noresponse_pictures"] = self._noresponse_pictures
        
        return outputs
    
if __name__ == "__main__":
    
    filename = "/media/data/2010reliability/fmri_logfiles/S1/MR16818.zip_FILES/MR16818-Line_Bisection.log"
    
    delay = 2.5*4
    
    pulses, pictures, correct_pictures, incorrect_pictures, noresponse_pictures = parse_line_bisection_log(filename, delay)
            
    
    print len(pulses), len(pictures["task"]), len(pictures["rest"]), len(correct_pictures["task"]), len(correct_pictures["rest"]),len(incorrect_pictures["task"]), len(incorrect_pictures["rest"]),len(noresponse_pictures["task"]), len(noresponse_pictures["rest"])
    print pictures["task"]
    print pictures["rest"]
    print correct_pictures["task"]
    print incorrect_pictures["task"]
    print noresponse_pictures["task"]
    

