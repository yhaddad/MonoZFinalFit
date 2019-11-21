import combine
import ROOT
import argparse

def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-d"  , "--datacard"   , type=str, required=True)
    parser.add_argument("-n"  , "--name"       , type=str, required=True)
    parser.add_argument("-a"  , "--asimov"     , action="store_true")
    parser.add_argument("-r"  , "--range"      , nargs='+', default=[0,10])
    parser.add_argument("-v"  , "--verbose"    , type=int, default=0)

    options = parser.parse_args()
    print (" -- datacard : ", options.datacard)
    print (" -- name     : ", options.name)
    print (" -- name     : ", options.asimov)
    combine.combine(
        options.datacard, mass=125,
        name = options.name,
        toys = -1 if options.asimov else 0,
        points =1000,
        robust_fit=True,
        #parameter_ranges="r={},{}".format(options.range[0], options.range[1]),
        verbose=options.verbose
    )

if __name__ == "__main__":
    main()
