import yaml
import ROOT
import uproot
import os
import math
import argparse
import ftool
from termcolor import colored
from pprint import pprint

ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gErrorIgnoreLevel=ROOT.kError

lumis = {
    "2016" : 35.9,
    "2017" : 41.5,
    "2018" : 60.0
}

def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i"  , "--input"   , type=str, default="config/inputs.yaml")
    parser.add_argument("-v"  , "--variable", type=str, default="measMET")
    parser.add_argument("-o"  , "--outdir"  , type=str, default="fitroom")
    parser.add_argument("-c"  , "--channel" , action="append")
    parser.add_argument("-s"  , "--signal"  , action="append")
    parser.add_argument("-t"  , "--stack"   , type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-tag", "--tag"     , type=str, default="ADD")
    parser.add_argument("-xs" , "--xsection", type=str, default="config/xsections_2017.yaml")

    options = parser.parse_args()
    # create a working directory where to store the datacards
    try:
        os.mkdir(options.outdir)
        print("Directory " , options.outdir ,  " Created ")
    except:
        if options.force:
            os.rmdir(options.outdir)
            os.mkdir(options.outdir)
            print "Directory " , options.outdir ,  " Re-created "

    inputs = None
    with open(options.input) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    xsections = None
    with open(options.xsection) as f:
        try:
            xsections = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    # make datasets per prcess
    datasets = {}
    options.stack = options.stack.split(",")
    nsignals = 0
    for dg in options.stack:
        print colored(" -- data group : " + inputs[dg]["type"] + " : " + dg, "green")
        p = ftool.DataGroup(
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"],
            variable   = options.variable,
            rebin      = 1,
            proc       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            xsections  = xsections,
            luminosity = lumis[options.era]
        )
        print " -------------- "
        print " Lumi  :", lumis[options.era]
        print " -------------- "
        if inputs[dg]["type"]=='signal':
            nsignals += 1
        datasets[dg] = p

    if options.stack is None:
        options.stack = ["WW", "ZZ", "WZ", "DY", "TOP", "Data"]

    ws = ftool.Workspace("ws.root", working_dir=options.outdir)
    ws.nSignals = nsignals
    for ch in options.channel:
        def bin_name(hist, ibin):
            return "bin{}to{}".format(
                int(hist.GetXaxis().GetBinLowEdge(ibin + 1)),
                int(hist.GetXaxis().GetBinUpEdge (ibin + 1))
            )
        def addNuisance(card, nuisName, process, rate):
            if nuisName not in card["nuisances"]:
                card["nuisances"][nuisName] = {}
            card["nuisances"][nuisName][process] = rate

        shapeHistName = "%s_%s" % (ch, options.variable)
        data_obs = datasets.get("Data").shape(ch, "nom")
        # print colored(" -- data_obs -->" + str(data_obs.Integral())+ " : " + ch, "yellow")
        # print colored(" -- WW  -->" + str(datasets.get("WW").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        # print colored(" -- DY  -->" + str(datasets.get("DY").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        # print colored(" -- ZZ  -->" + str(datasets.get("ZZ").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        # print colored(" -- WZ  -->" + str(datasets.get("WZ").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        # print colored(" -- VVV -->" + str(datasets.get("VVV").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        # print colored(" -- TOP -->" + str(datasets.get("TOP").shape(ch, "nom").Integral())+ " : " + ch, "blue")
        for ibin in range(data_obs.GetNbinsX()):
            channel = "%s_%s" % (ch, bin_name(data_obs, ibin))
            if ch in ['catSignal-0jet', 'catSignal-1jet']:
                channel = channel.replace("jet","")
                channel = channel.replace("catSignal","BSM")
                channel = channel.replace("-","")
            ws.addChannel(channel)
            card = ws.cards[channel]
            card["observation"].append("bin          %s"    % channel)
            card["observation"].append("observation  %1.3f" % int(data_obs.GetBinContent(ibin+1)) )

        def addNominal(process):
            nominalHist = datasets.get(process).shape(ch, "nom")
            shapeName = "%s_%s" % (process, ch)
            ftool.checkShape(nominalHist, shapeName)
            for ibin in range(nominalHist.GetNbinsX()):
                channel = "%s_%s" % (ch, bin_name(nominalHist, ibin))
                if ch in ['catSignal-0jet', 'catSignal-1jet']:
                    channel = channel.replace("jet","")
                    channel = channel.replace("catSignal","BSM")
                    channel = channel.replace("-","")

                card = ws.cards[channel]
                b = nominalHist.GetBinContent(ibin + 1)
                card["rates"].append((process, b))
                e = nominalHist.GetBinError(ibin + 1)
                if math.isnan(b) or math.isnan(e):
                    print("Warning: NAN found in %s_%s (%.0f-%.0f)" % (
                        process, channel, nominalHist.GetXaxis().GetBinLowEdge(ibin + 1),
                        nominalHist.GetXaxis().GetBinUpEdge(ibin + 1)
                    ))
                    continue
                if b == 0.:
                    print("Warning: Zero bin in %s_%s (%.0f-%.0f)" % (
                        process, channel, nominalHist.GetXaxis().GetBinLowEdge(ibin + 1),
                        nominalHist.GetXaxis().GetBinUpEdge(ibin + 1)
                    ))
                else:
                    addNuisance(card, "McStat_%s_%s lnN" % (channel, process), process, 1.+e/b)

        def addShapeNuisance(process, nuisance, cardName, ):
            #print colored(" + adding nuisance : " + nuisance, "blue")
            histUp, histDown = datasets.get(process).shape(ch, nuisance)
            nominalHist = datasets.get(process).shape(ch, "nom")
            try:
                hupratio = histUp.Clone("tmpratio1")
                hupratio.Divide(nominalHist)
                hdownratio = histDown.Clone("tmpratio2")
                hdownratio.Divide(nominalHist)
            except:
                return
            shapeName = "%s_%s_%sUp" % (process, ch, cardName)
            ftool.checkShape(histUp, shapeName)

            shapeName = "%s_%s_%sDown" % (process, ch, cardName)
            ftool.checkShape(histDown, shapeName)

            for iBin in range(nominalHist.GetNbinsX()):
                channel = "%s_%s" % (ch, bin_name(nominalHist, iBin))
                if ch in ['catSignal-0jet', 'catSignal-1jet']:
                    channel = channel.replace("jet","")
                    channel = channel.replace("catSignal","BSM")
                    channel = channel.replace("-","")

                card = ws.cards[channel]
                upR = hupratio.GetBinContent(iBin + 1)
                if upR <= 0:
                   upR = 1.0
                downR = hdownratio.GetBinContent(iBin + 1)
                if downR <= 0:
                   downR = 1.0
                addNuisance(card, "%s lnN" % cardName, process, (upR, downR))

        for p, pg in  datasets.items():
            #print colored(" -> " + p, "red")
            if 'data'   in pg.ptype: continue
            #if 'signal' in pg.ptype: continue
            addNominal(p)
            # we need to add more systematics here
            # -- objects
            addShapeNuisance(p, "ElectronEn", "CMS_res_e")
            addShapeNuisance(p, "ElecronSF" , "CMS_eff_e")
            addShapeNuisance(p, "MuonEn"    , "CMS_res_m")
            addShapeNuisance(p, "MuonSF"    , "CMS_eff_m")
            # -- jets/met
            addShapeNuisance(p, "jesTotal"  , "CMS_JES_{}".format(options.era))
            addShapeNuisance(p, "jer"       , "CMS_JER_{}".format(options.era))
            addShapeNuisance(p, "unclustEn" , "CMS_UES_{}".format(options.era))
            # -- trigger and bjets
            addShapeNuisance(p, "btagEventWeight", "CMS_BTag_{}".format(options.era))
            addShapeNuisance(p, "TriggerSFWeight", "CMS_Trigger_{}".format(options.era))
            addShapeNuisance(p, "PrefireWeight"  , "CMS_PrefireWeight_{}".format(options.era))
            # -- thoery uncert
            addShapeNuisance(p, "EWK"  , "EWKZZWZ")
            addShapeNuisance(p, "PDF"  , "PDF")
            # -- pu/vtx reweighting
            addShapeNuisance(p, "nvtxWeight", "CMS_PU")
            addShapeNuisance(p, "puWeight"  , "CMS_PU")
            for iBin in range(data_obs.GetNbinsX()):
                bn = bin_name(data_obs, iBin)
                channel = "%s_%s" % (ch, bn)
                if ch in ['catSignal-0jet', 'catSignal-1jet']:
                    channel = channel.replace("jet","")
                    channel = channel.replace("catSignal","BSM")
                    channel = channel.replace("-","")
                card = ws.cards[channel]
                if options.era == "2016":
                    addNuisance(card, "CMS_lumi_2016 lnN".format(options.era), p, 1.025)
                if options.era == "2017":
                    addNuisance(card, "CMS_lumi_2017 lnN".format(options.era), p, 1.023)
                if options.era == "2018":
                    addNuisance(card, "CMS_lumi_2018 lnN".format(options.era), p, 1.025)
                addNuisance(card, "CMS_EUPS      lnN".format(options.era), p, 1.02)
        # Uncorrelated theory uncertainties in signal and main backgrounds
        theory_bkgs = []
        signalGroup = [ c for i, c in datasets.items() if c.ptype=="signal"]
        if ch in ['EE', 'MM', '2L', '3L']:
            theory_bkgs.append(datasets.get("WZ3lnu"))
        if ch in ['EE', 'MM', 'NRB']:
            theory_bkgs.append(datasets.get("qqZZ2l2nu"))
        if ch in ['4L']:
            theory_bkgs.append(datasets.get("qqZZ4l"))

        # for pg in theory_bkgs + signalGroup:
        #     process = pg.proc
        #     print("-----:: ", process)
        #     if 'DM' in process or 'ADD' in process:
        #         for iBin in range(data_obs.GetNbinsX()):
        #             bn = bin_name(data_obs, iBin)
        #             channel = "%s_%s" % (ch, bn)
        #             if ch in ['catSignal-0jet', 'catSignal-1jet']:
        #                 channel = channel.replace("jet","")
        #                 channel = channel.replace("catSignal","BSM")
        #                 channel = channel.replace("-","")
        #
        #             card = ws.cards[channel]
        #             #addNuisance(card, "Theo_pdfAlphaS_%s lnN" % process, process, 1.01)
        #             #addNuisance(card, "Theo_factRenormScale_%s lnN" % process, process, 1.05)
        #     # this now commented as it is not yet implemented in our code
        #     #if process in ['WZ3lnu', 'qqZZ2l2nu', 'qqZZ4l']:
        #     #    addShapeNuisance(process, "factRenormScale", "Theo_factRenormScale_VV")
        #     #else:
        #     #    addShapeNuisance(process, "factRenormScale", "Theo_factRenormScale_%s" % process)

        for iBin in range(data_obs.GetNbinsX()):
            bn = bin_name(data_obs, iBin)
            channel = "%s_%s" % (ch, bn)
            if ch in ['catSignal-0jet', 'catSignal-1jet']:
                channel = channel.replace("jet","")
                channel = channel.replace("catSignal","BSM")
                channel = channel.replace("-","")

            card = ws.cards[channel]
            if "BSM" in channel:# ch2
                card["extras"].add("CMS_emnorm_{}  rateParam BSM* EM 1 [0.1,10]".format(options.era))
                card["extras"].add("CMS_vvnorm_{}  rateParam BSM* ZZ 1 [0.1,10]".format(options.era))
                card["extras"].add("CMS_vvnorm_{}  rateParam BSM* WZ 1 [0.1,10]".format(options.era))
            elif "cat3L" in channel: # ch5
                card["extras"].add("CMS_vvnorm_{}  rateParam cat3L* ZZ 1 [0.1,10]".format(options.era))
                card["extras"].add("CMS_vvnorm_{}  rateParam cat3L* WZ 1 [0.1,10]".format(options.era))
            elif "cat4L" in channel: # ch8
                card["extras"].add("CMS_vvnorm_{}  rateParam cat4L* ZZ 1 [0.1,10]".format(options.era))
            elif "catEM" in channel:
                card["extras"].add("CMS_emnorm_{}  rateParam catEM* EM 1 [0.1,10]".format(options.era))

    ws.write(makeGroups=False)



if __name__ == "__main__":
    main()
