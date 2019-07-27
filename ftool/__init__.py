import ROOT
import uproot
import os
import sys
import numpy as np
from termcolor import colored
from pprint import pprint

def checkShape(shapeHist, name):
    negativeBins = False
    zeroBins = False
    for iBin in range(shapeHist.GetNbinsX()):
        b = shapeHist.GetBinContent(iBin + 1)
        if b < 0.:
            negativeBins = True
            shapeHist.SetBinContent(iBin + 1, 0.)
            shapeHist.SetBinError(iBin + 1, -b)
        elif b == 0.:
            zeroBins = True
    if shapeHist.GetBinContent(0) != 0.:
        shapeHist.SetBinContent(0, 0.)
    if shapeHist.GetBinContent(shapeHist.GetNbinsX()+1) != 0.:
        shapeHist.SetBinContent(shapeHist.GetNbinsX()+1, 0.)

def get_scale(infile, xsections, lumi=1.0):
    _uproot_file = uproot.open(infile)
    # getting the luminosity wright
    scale = lumi/_uproot_file["Runs"].array("genEventCount").sum()
    # removing the old normalisation and using new xsection
    original_xsec = abs(_uproot_file["Events"].array("xsecscale")[0])
    xsec  = xsections[os.path.basename(infile.replace(".root", ""))]["xsec"]
    xsec *= xsections[os.path.basename(infile.replace(".root", ""))]["kr"]
    xsec *= xsections[os.path.basename(infile.replace(".root", ""))]["br"]
    xsec *= 1000.0
    # getting the negative/positive weight fractions
    pos_fraction = np.mean(
        (1.0+_uproot_file["Events"].array("xsecscale")/original_xsec)/2.0
    )
    scale *= xsec/original_xsec
    scale /= pos_fraction
    return scale


def print_hist(hist):
    st = ",".join([ str(hist.GetBinContent(ibin)) for ibin in range(1, 3)])
    st = "first 2 bins : " + st
    print colored(st, "blue")


class DataGroup:
    def __init__(self, files, variable="measMET", proc="DY", rebin=1, kfactor=1.,
                 ptype="background", luminosity=1.0, normalise=True, xsections=None):
        self._names = files
        self.proc = proc
        self.ptype = ptype
        self.hists  = dict()
        self.outfile = None
        if False:
            print " -- variable  : ", variable
            print " -- proc      : ", proc
            print " -- kfactor   : ", kfactor
            print " -- ptype     : ", ptype
            print " -- lumi      : ", luminosity
            print " -- normalise : ", normalise

        for fn in self._names:
            _proc = os.path.basename(fn).replace(".root","")
            _file = ROOT.TFile.Open(fn)
            if not _file:
                raise "%s is not a valid rootfile" % self._name
            _scale = 1.0
            if ptype.lower() != "data":
                _scale  = get_scale(fn, xsections=xsections, lumi=luminosity)
                _scale *= kfactor
            for key in _file.GetListOfKeys():
                if "TH1" in key.GetClassName() :
                    if variable not in key.GetName():
                        continue
                    roothist = key.ReadObj()
                    roothist.Sumw2()
                    roothist.Scale(_scale)
                    name = key.GetName().replace(_proc, self.proc)
                    name = name if 'sys' in name else name + "_nom"
                    if ptype.lower() == "signal":
                        name = name.replace(proc, "DM")
                    if "catSignal-0jet" in name:
                        name = name.replace("catSignal-0jet", "BSM0")
                    if "catSignal-1jet" in name:
                        name = name.replace("catSignal-1jet", "BSM1")
                    roothist.SetName(name.replace("nom",""))
                    roothist.SetDirectory(0)
                    ROOT.SetOwnership(roothist, 0)
                    if rebin > 1:
                        roothist.Rebin(rebin)
                    if name in self.hists.keys():
                        self.hists[name].Add(roothist)
                    else:
                        self.hists[name] = roothist

    def histograms(self):
        """
        returning all the histograms in the datasets
        """
        return self.hists

    def shape(self, channel, systvar="nom"):
        shapeUp, shapeDown= None, None
        for n, hist in self.hists.items():
            if systvar in n and systvar=="nom" and channel in n:
                return hist
            elif channel in n and systvar in n:
                if "Up" in n:
                    shapeUp = hist
                if "Down" in n:
                    shapeDown= hist
        return (shapeUp, shapeDown)

    def rootfile(self):
        return self.outfile

    def save(self, filename=None, working_dir="fitroom"):
        if not filename:
            filename = self.proc + ".root"
        self.outfile = filename
        fout = ROOT.TFile(working_dir + "/" + filename, "recreate")
        fout.cd()
        for name, hist in self.hists.items():
            hist.Write()
        fout.Write()
        fout.Close()

class DataCard:
    def __init__(self, fileName, working_dir="fitroom"):
        self.cards = {}
        self.nSignals = 0
        self.working_dir = working_dir
    def addChannel(self, channel):
        self.cards[channel] = {
            "shapes": [],
            "observation": [],
            "rates": [],  # To be a tuple (process name, rate), signals first!
            "nuisances": {},  # To be a dict "nuisance name": {"process name": scale, ...}
            "extras": set(),
        }
    def write(self, makeGroups=False):
        for channel, card in self.cards.items():
            with open(self.working_dir + "/card_%s" % channel, "w") as fout:
                # Headers
                fout.write("# Card for channel %s\n" % channel)
                fout.write("imax 1 # process in this card\n")
                fout.write("jmax %d # process in this card - 1\n" % (len(card["rates"])-1, ))
                fout.write("kmax %d # nuisances in this card\n" % len(card["nuisances"]))
                fout.write("-"*30 + "\n")
                for line in card["shapes"]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                for line in card["observation"]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                binLine = "{0:<40}".format("bin")
                procLine = "{0:<40}".format("process")
                indexLine = "{0:<40}".format("process")
                rateLine = "{0:<40}".format("rate")
                for i, tup in enumerate(card["rates"]):
                    binLine += "{0:>15}".format(channel)
                    procLine += "{0:>15}".format(tup[0])
                    indexLine += "{0:>15}".format(i - self.nSignals + 1)
                    rateLine += "{0:>15}".format("%.3f" % tup[1])
                for line in [binLine, procLine, indexLine, rateLine]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                for nuisance in sorted(card["nuisances"].keys()):
                    processScales = card["nuisances"][nuisance]
                    line = "{0:<40}".format(nuisance)
                    for process, _ in card["rates"]:
                        if process in processScales:
                            line += "{0:>15}".format("%.3f" % processScales[process])
                        else:
                            line += "{0:>15}".format("-")
                    fout.write(line+"\n")
                def makeGroups(name, prefix):
                    group = [n.split(" ")[0] for n in card["nuisances"].keys() if prefix in n]
                    fout.write("%s group = %s\n" % (name, " ".join(group)))
                #makeGroups("theory", "Theo_")
                #makeGroups("mcStat", "Stat_")
                #makeGroups("CMS", "CMS_")
                for line in card["extras"]:
                    fout.write(line+"\n")

class Workspace:
    def __init__(self, fileName, working_dir="fitroom"):
        self.cards = {}
        self.nSignals = 0
        self.working_dir = working_dir

    def addChannel(self, channel):
        self.cards[channel] = {
            "shapes": [],
            "observation": [],
            "rates": [],  # To be a tuple (process name, rate), signals first!
            "nuisances": {},  # To be a dict "nuisance name": {"process name": scale, ...}
            "extras": set(),
        }
    def write(self, makeGroups=False):
        for channel, card in self.cards.items():
            with open(self.working_dir + "/card_%s" % channel, "w") as fout:
                # Headers
                fout.write("# Card for channel %s\n" % channel)
                fout.write("imax 1 # process in this card\n")
                fout.write("jmax %d # process in this card - 1\n" % (len(card["rates"])-1, ))
                fout.write("kmax %d # nuisances in this card\n" % len(card["nuisances"]))
                fout.write("-"*30 + "\n")
                for line in card["shapes"]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                for line in card["observation"]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                binLine = "{0:<40}".format("bin")
                procLine = "{0:<40}".format("process")
                indexLine = "{0:<40}".format("process")
                rateLine = "{0:<40}".format("rate")
                for i, tup in enumerate(card["rates"]):
                    binLine += "{0:>20}".format(channel)
                    procLine += "{0:>20}".format(tup[0])
                    indexLine += "{0:>20}".format(i - self.nSignals + 1)
                    rateLine += "{0:>20}".format("%.3f" % tup[1])
                for line in [binLine, procLine, indexLine, rateLine]:
                    fout.write(line+"\n")
                fout.write("-"*30 + "\n")
                for nuisance in sorted(card["nuisances"].keys()):
                    processScales = card["nuisances"][nuisance]
                    line = "{0:<40}".format(nuisance)
                    for process, _ in card["rates"]:
                        if process in processScales:
                            s = processScales[process]
                            if type(s) is tuple:
                                if (s[0] <= 0) or (s[1] <= 0):
                                    line += "{0:>20}".format("-")
                                else:
                                    line += "{0:>20}".format("%.3f/%.3f" % s)
                            else:
                                line += "{0:>20}".format("%.3f" % s)
                        else:
                            line += "{0:>20}".format("-")
                    fout.write(line.replace("0.000/0.000", "0.100/0.100").replace("0.000", "0.100")+"\n")
                if makeGroups:
                    def makeGroups(name, prefix):
                        group = [n.split(" ")[0] for n in card["nuisances"].keys() if prefix in n]
                        fout.write("%s group = %s\n" % (name, " ".join(group)))
                    makeGroups("theory", "Theo_")
                    makeGroups("mcStat", "Stat_")
                    makeGroups("CMS", "CMS_")
                for line in card["extras"]:
                    fout.write(line+"\n")
