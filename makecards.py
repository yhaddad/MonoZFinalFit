import yaml
import glob
import os




options_input    = "config/inputs-redumption-ERA.yaml"
inputs = None


def combine_cards(model):
    os.system("rm -f {}".format(model))
    print("model : ", model )
    command = "./combineCards.py {}".format(model)
    command = command.replace("combined.dat", "shapes-*.dat")
    command = command + " > {}".format(model)
    print(command)
    os.system(command)



for year in [2016]:
    with open(options_input.replace("ERA", str(year))) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    for n, sam in inputs.items():
        if sam["type"] == "signal" and "ADD" in n:
            print(" ++++ processig : ", n)
            os.system(
        		"python3 makeDataCard.py --channel catSignal-0jet catSignal-1jet"
        		" --stack {signal} ZZ WZ WW VVV NonResonant DY data "
        		"--input=config/inputs-redumption-{era}.yaml --era={era}".format(signal=n, era=year))
            os.system(
        		"python3 makeDataCard.py --channel cat3L "
        		"--stack {signal} ZZ WZ WW VVV NonResonant DY data "
        		"--input=config/inputs-redumption-{era}.yaml --era={era}".format(signal=n, era=year))
            os.system(
        		"python3 makeDataCard.py --channel cat4L "
        		"--stack {signal} ZZ WZ WW VVV NonResonant DY data "
        		"--input=config/inputs-redumption-{era}.yaml --era={era}".format(signal=n, era=year))
            os.system(
        		"python3 makeDataCard.py --channel catEM "
        		"--stack {signal} ZZ WZ WW VVV NonResonant DY data "
        		"--input=config/inputs-redumption-{era}.yaml --era={era}".format(signal=n, era=year))
