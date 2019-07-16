#!/usr/bin/env python3

import ROOT
import uproot
import collections
from termcolor import colored
import math
#import argparse
import yaml
import os
import numpy as np

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.gROOT.ProcessLine(".x rootlogon.C")
ROOT.gErrorIgnoreLevel=ROOT.kError


#parser = argparse.ArgumentParser("")
#parser.add_argument('-era', '--era', type=str, default="2018", help="")
#parser.add_argument('-cfg', '--cfg', type=str, default="./config/inputs-NanoAODv4.yaml", help="")
#parser.add_argument('--doxsec', action='store_true',  dest='doxsec', default=False)
#options  = parser.parse_args()

processes = {}
with open("./config/inputs-NanoAODv4.yaml", 'r') as stream:
    processes = yaml.safe_load(stream)

xsections = {}
with open("./config/xsections_{}.yaml".format(2017), 'r') as stream:
    xsections = yaml.safe_load(stream)

error_band_color           = 138
error_band_style           = 3357
error_band_opacity         = 1

syst_error_band_color      = 139
syst_error_band_style      = 3357
syst_error_band_opacity    = 1

canvas_width               = 600
canvas_height              = 600+100
ratio_error_same           = False
ratio_syst_band_color      = 138
ratio_syst_band_style      = 1001
ratio_error_band_color     = 139
ratio_error_band_style     = 1001
ratio_error_band_opacity   = 0.7
ratio_draw_signal          = False
ratio_precision_range      = [0, 2.6]
ratio_plot_grid            = True
text_font                  = 43
text_size                  = 18

systematics_sources = [
    "ElectronEn",
    "MuonEn",
    "jesTotal",
    "jer",
    "unclustEn",
    "puWeight",
    "PDF",
    "MuonSF",
    "ElecronSF",
    "EWK",
    "nvtxWeight",
    "TriggerSFWeight",
    "btagEventWeight",
]

observable = {
    "catSignal-0jet"  : "measMET",
    "catEM"           : "measMET",
    "catSignal-1jet"  : "measMET",
    "cat3L"           : "measMET",
    "cat4L"           : "measMET",
    "catNRB"          : "measMET",
    "catTOP"          : "measMET",
    "catDY"           : "measMET",
    "njet"            : "njet",
    "balance"         : "balance",
    "phizmet"         : "phizmet"
}

names = {
    "catSignal-0jet"  : "MET (GeV)",
    "catSignal-1jet"  : "MET (GeV)",
    "catEM"  : "MET (GeV)",
    "cat3L"  : "emulated MET (GeV)",
    "cat4L"  : "emulated MET (GeV)",
    "catNRB" : "MET (GeV)",
    "catTOP" : "MET (GeV)",
    "catDY"  : "MET (GeV)",
    "njet"   : "N_{jet}",
    "balance": "balance",
    "phizmet": "#phi(Z,p_{T}^{miss})"
}

ranges = {
    "catSignal-0jet"  : [100, 1000],
    "catSignal-1jet"  : [100, 1000],
    "catEM"  : [ 50, 1000],
    "cat3L"  : [ 50, 1000],
    "cat4L"  : [ 50, 1000],
    "catNRB" : [ 50, 100],
    "catTOP" : [ 50, 100],
    "catDY"  : [ 50, 100],
    "njet"   : [  0,   6],
    "balance": [  0,   2],
    "phizmet": [  0,   4]
}

def get_channel_title(text):
    text = text.replace("_","")
    cat = {
        "catSignal-0jet" : "0 jets",
        "catEM" : "e#mu"  ,
        "catSignal-1jet" : "1 jets",
        "cat3L" : "WZ"    ,
        "cat4L" : "ZZ"    ,
        "catNRB": "NRB"   ,
        "catTOP": "TOP"   ,
        "catDY" : "DY"    ,
        "njet"  : "N_{jets}",
        "balance" : "balance",
        "phizmet": "phizmet"

    }
    return cat[text]

def customizeHisto(hist, ratioplot = True):
    hist.GetYaxis().SetTitleSize  (21)
    hist.GetYaxis().SetTitleFont  (43)
    hist.GetYaxis().SetTitleOffset(1.8)
    hist.GetYaxis().SetLabelFont  (43)
    hist.GetYaxis().SetLabelSize  (18)
    hist.GetXaxis().SetTitleSize  (21)
    hist.GetXaxis().SetTitleFont  (43)
    hist.GetXaxis().SetTitleOffset(3.5)
    hist.GetXaxis().SetLabelOffset(0.02)
    hist.GetXaxis().SetLabelFont  (43)
    hist.GetXaxis().SetLabelSize  (18)

def draw_cms_headlabel(label_left  ='#scale[1.2]{#bf{CMS}} #it{Preliminary}',
                       label_right ='#sqrt{s} = 13 TeV, L = 2.56 fb^{-1}'):
    tex_left  = ROOT.TLatex()
    tex_left.SetTextAlign (11);
    tex_left.SetTextFont  (42);
    tex_left.SetTextSize  (0.036);
    tex_right = ROOT.TLatex()
    tex_right.SetTextAlign(31);
    tex_right.SetTextFont (42);
    tex_right.SetTextSize (0.036);
    tex_left.DrawLatexNDC (0.14,
                           1.01 - ROOT.gStyle.GetPadTopMargin(),label_left)
    tex_right.DrawLatexNDC(1-0.05,
                           1.01 - ROOT.gStyle.GetPadTopMargin(),label_right)

def makeRatio(hist1,hist2,ymax=2.1,ymin=0,norm=False, isdata =False):
    """returns the ratio plot hist2/hist1
    if one of the histograms is a stack put it in as argument 2!"""
    if norm:
        try:
            hist1.Scale(1/hist1.Integral())
            hist2.Scale(1/hist2.Integral())
        except(ZeroDivisionError):
            pass
    retH = hist1.Clone()
    retH.Divide(hist2)
    if isdata:
        for ibin in range(hist2.GetNbinsX()+1):
            ymc  = hist2.GetBinContent(ibin);
            stat = hist1.GetBinError  (ibin);
            if (ymc>0):
                retH.SetBinError  (ibin,stat/ymc);
            else:
                retH.SetBinError  (ibin,0);
    ROOT.SetOwnership(retH,0)
    return retH

def draw_error_band(myHisto,systematics={},systematic_only=True, combine_with_systematic=True):
    """
    Draw this histogram with the statistical
    precision error in each bin
    """

    statPrecision = myHisto.Clone('_statErrors_')
    ROOT.SetOwnership(statPrecision,0)
    statPrecision.SetFillColorAlpha(error_band_color,error_band_opacity)
    statPrecision.SetFillStyle(error_band_style)
    statPrecision.SetLineWidth(2)
    statPrecision.SetMarkerColorAlpha(0,0)

    systPrecision = myHisto.Clone('_systErrors_')
    ROOT.SetOwnership(systPrecision,0)
    systPrecision.SetFillColorAlpha(syst_error_band_color,syst_error_band_opacity)
    systPrecision.SetFillStyle(syst_error_band_style)
    systPrecision.SetLineWidth(2)
    systPrecision.SetMarkerColorAlpha(0,0)


    if combine_with_systematic : systematic_only = True
    if systematic_only:
        for ibin in range(myHisto.GetNbinsX()+1):
            y    = statPrecision.GetBinContent(ibin);
            stat = statPrecision.GetBinError  (ibin);

            up_err_sum2 = stat**2
            dw_err_sum2 = stat**2
            for key, syst in systematics.items():
                up_diff   = syst.get("Up").GetBinContent(ibin)   - y
                dw_diff   = syst.get("Down").GetBinContent(ibin) - y
                if up_diff > 0 :
                    up_err_sum2 += up_diff*up_diff
                if dw_diff < 0 :
                    dw_err_sum2 += dw_diff*dw_diff
            up_error = math.sqrt(up_err_sum2)
            dw_error = math.sqrt(dw_err_sum2)

            band_max   = y + up_error
            band_min   = y - dw_error

            systPrecision.SetBinContent(ibin, (band_max + band_min)/2.0);
            systPrecision.SetBinError  (ibin, (band_max - band_min)/2.0);

            statPrecision.SetBinContent(ibin,   y    )
            statPrecision.SetBinError  (ibin,   stat )
            # ------
    return (statPrecision, systPrecision)

def make_stat_progression(myHisto,systematics={},
                          systematic_only=True,
                          combine_with_systematic=True):
    """
        This function returns a function with
        the statistical precision in each bin
    """

    statPrecision = myHisto.Clone('_ratioErrors_')
    systPrecision = myHisto.Clone('_ratioSysErrors_')
    statPrecision.SetFillColorAlpha(ratio_error_band_color,ratio_error_band_opacity)
    statPrecision.SetFillStyle(ratio_error_band_style)
    statPrecision.SetMarkerColorAlpha(0,0)
    systPrecision.SetFillColorAlpha(ratio_syst_band_color,ratio_error_band_opacity)
    systPrecision.SetFillStyle(ratio_syst_band_style)
    systPrecision.SetMarkerColorAlpha(0,0)

    if len(systematics)==0 : systematic_only = False
    for ibin in range(myHisto.GetNbinsX()+1):
        y    = statPrecision.GetBinContent(ibin)
        stat = statPrecision.GetBinError  (ibin)
        if( y > 0 ):
            statPrecision.SetBinContent(ibin,      1 )
            statPrecision.SetBinError  (ibin, stat/y )
        else:
            statPrecision.SetBinContent(ibin,   1 )
            statPrecision.SetBinError  (ibin,   0 )
        if systematic_only:
            up_err_sum2 = 0
            dw_err_sum2 = 0
            if( y > 0 ):
                up_err_sum2 = (stat/y)*(stat/y)
                dw_err_sum2 = (stat/y)*(stat/y)
                for key, syst in systematics.items():
                    up_diff   = (syst.get("Up"  ).GetBinContent(ibin)- y)/y
                    dw_diff   = (syst.get("Down").GetBinContent(ibin)- y)/y
                    if( up_diff > 0 ):
                        up_err_sum2  += up_diff*up_diff
                    if( dw_diff < 0 ):
                        dw_err_sum2  += dw_diff*dw_diff
            up_error = math.sqrt(up_err_sum2)
            dw_error = math.sqrt(dw_err_sum2)
            band_max   = 1 + up_error
            band_min   = 1 - dw_error
            systPrecision.SetBinContent(ibin, (band_max + band_min)/2.0);
            systPrecision.SetBinError  (ibin, (band_max - band_min)/2.0);
    statPrecision.GetYaxis().SetRangeUser(0, 2)
    systPrecision.GetYaxis().SetRangeUser(0, 2)
    
    return (statPrecision, systPrecision)

def makeRatioPlotCanvas(name=''):
    """
    returns a divided canvas for ratios
    """
    canv  = ROOT.TCanvas("c_" + name, name, canvas_width, canvas_height)
    canv.cd()
    padup = ROOT.TPad("padup", "padup", 0, 0.3, 1, 1.0)
    padup.SetNumber(1)
    paddw = ROOT.TPad("paddw", "paddw", 0, 0.0, 1, 0.3)
    paddw.SetNumber(2)
    padup.Draw()
    padup.SetTopMargin(0.08)
    padup.SetBottomMargin(0.00)
    padup.SetLeftMargin(0.14)
    padup.SetRightMargin(0.05)
    padup.SetFrameBorderMode(0)
    padup.SetFrameBorderMode(0)
    paddw.Draw()
    paddw.SetTopMargin(0.00)
    paddw.SetBottomMargin(0.37)
    paddw.SetLeftMargin(0.14)
    paddw.SetRightMargin(0.05)
    paddw.SetFrameBorderMode(0)
    canv.cd()
    ROOT.SetOwnership(padup,0)
    ROOT.SetOwnership(paddw,0)
    return canv

def check_nuisance(process, nuisance, ch, hist_nm, hist_up, hist_dw):
    c = makeRatioPlotCanvas(process)
    c.cd(1)
    _htmp_ = hist_nm.Clone('__htmp__')
    ROOT.SetOwnership(_htmp_, 0)
    _htmp_.Reset()
    _ymax_ = max([x.GetMaximum() for x in [hist_nm, hist_up, hist_dw]])
    _ymin_ = min([x.GetMinimum() for x in [hist_nm, hist_up, hist_dw]])
    
    _ymin_ = (0.01 - 0.003) if _ymin_ <= 0 else _ymin_
    _ymax_ = _ymax_*1000
    
    _htmp_.GetYaxis().SetRangeUser(_ymin_,_ymax_)
    ROOT.gPad.SetLogy()

    customizeHisto(_htmp_)
    _htmp_.Draw('hist')
        
    hup_ratio = hist_up.Clone("hratio_up")
    hup_ratio.Divide(hist_nm)
    hup_ratio.SetLineColor(ROOT.kRed)
    hup_ratio.SetLineWidth(2)
    hup_ratio.SetFillStyle(0)
    
    hdw_ratio = hist_dw.Clone("hratio_dw")
    hdw_ratio.Divide(hist_nm)
    hdw_ratio.SetLineColor(ROOT.kBlue)
    hdw_ratio.SetLineWidth(2)
    hdw_ratio.SetFillStyle(0)
    
    hist_nm.SetTitle("_".join([process,nuisance,ch]))
    #customizeHisto(hist_nm)
    hist_nm.SetLineColor(ROOT.kBlack)
    hist_nm.SetLineStyle(1)
    hist_nm.SetLineWidth(2)
    hist_nm.SetFillStyle(0)
    hist_nm.Draw("hist,same")

    #customizeHisto(hist_up)
    hist_up.SetLineColor(ROOT.kRed)
    hist_up.SetLineWidth(2)
    hist_up.SetFillStyle(0)
    hist_up.Draw("hist,same")

    #customizeHisto(hist_dw)
    hist_dw.SetLineColor(ROOT.kBlue)
    hist_dw.SetLineWidth(2)
    hist_dw.SetFillStyle(0)
    hist_dw.Draw("hist,same")

    if hist_nm.Integral() != 0:
        t = ROOT.TLatex()
        t.SetTextAlign(13)
        t.SetTextFont (text_font)
        t.SetTextSize (text_size)
        
        text = "lnN {:1.3f}/{:1.3f}".format(
            hist_up.Integral()/hist_nm.Integral(),
            hist_dw.Integral()/hist_nm.Integral()
        )
        t.DrawLatexNDC(
            (0.02 + ROOT.gStyle.GetPadLeftMargin()),
            (0.93 - ROOT.gStyle.GetPadTopMargin()),
            text
        )
    ROOT.gPad.RedrawAxis()
    c.cd(2)
    hup_ratio.GetYaxis().SetTitle("Ratio")
    hup_ratio.SetTitle("")
    hdw_ratio.SetTitle("")
    
    hup_ratio.GetYaxis().SetRangeUser(0, 2)
    hup_ratio.GetYaxis().SetTitle('Data/MC')
    hup_ratio.GetYaxis().CenterTitle(True)

    customizeHisto(hup_ratio)
    customizeHisto(hdw_ratio)
     
    hup_ratio.Draw("hist")
    hdw_ratio.Draw("histsame")
    
    if not os.path.exists("shape_check"):
        os.makedirs("shape_check")

        ROOT.gPad.RedrawAxis()
    c.SaveAs("shape_check/shape_{}_{}_{}.png".format(process, ch, nuisance))
    c.SaveAs("shape_check/shape_{}_{}_{}.pdf".format(process, ch, nuisance))
    

def drawing(channel="_3L", ylog=True, lumi=41.5, blind=True):
    print " @@@@@@ running the {} channel".format(channel)
    x_vec = collections.OrderedDict()
    w_vec = collections.OrderedDict()
    
    _size_ = (len(processes) / 4) * 0.08
    root_legend  = ROOT.TLegend(
        0.35, (0.96 - ROOT.gStyle.GetPadTopMargin()) - _size_,
        (1.10 - ROOT.gStyle.GetPadRightMargin()),
        (0.94 - ROOT.gStyle.GetPadTopMargin()))
    root_legend.SetNColumns(4)
    root_legend.SetColumnSeparation(-0.5)

    first = 0
    
    for procname, cmd  in processes.items():
        if "data" in procname.lower(): continue
        #print "process : ", procname
        files     = cmd["files"]
        hist_nom  = None
        root_histos_syst = {}
        for fn in files:
            print " -- file : ", fn
            fn_root = uproot.open(fn)
            bn_root = ROOT.TFile.Open(fn)
            hist_names = []
            syst_names = []
            for nm in fn_root.keys():
                if 'sys' in str(nm):
                    syst_names.append(str(nm.decode('UTF-8')))
                    continue
                if channel not in str(nm):
                    continue
                if observable[channel.replace('_','')] not in str(nm):
                    continue
                hist_names.append(str(nm.decode('UTF-8')))
            
            for hist_name in hist_names:
                hname = hist_name.replace("b'","")
                hname = hname.replace(";1","")
                hist  = bn_root.Get(hname)
                
                hist.SetDirectory(0)
                if cmd.get("type") != "data":
                    scale = lumi/fn_root["Runs"].array("genEventCount").sum()
                    original_xsec = abs(fn_root["Events"].array("xsecscale")[0])
                    xsec  = xsections[os.path.basename(fn.replace(".root", ""))]["xsec"]
                    xsec *= xsections[os.path.basename(fn.replace(".root", ""))]["kr"]
                    xsec *= xsections[os.path.basename(fn.replace(".root", ""))]["br"]
                    xsec *= 1000.0
                    print colored(
                        "xsec={:1.3f} : {:1.3f}".format(
                            xsec,
                            original_xsec
                        ),
                        "green"
                    )
                    
                    scale *= xsec/original_xsec
                    scale /= np.mean((1.0+fn_root["Events"].array("xsecscale")/original_xsec)/2.0)
                    scale *= cmd.get("kfactor", 1.0)
                    
                    hist.Sumw2()
                    hist.Scale(scale)
                    for syst in systematics_sources:
                        if not any(syst in x  for x in syst_names):
                            continue
                        _h_syst_up = bn_root.Get(hname+"_sys_"+syst+"Up")
                        _h_syst_up.SetDirectory(0)
                        _h_syst_up.Sumw2()
                        _h_syst_up.Scale(scale)
                                                
                        _h_syst_dw = bn_root.Get(hname + "_sys_"+syst+"Down")
                        _h_syst_dw.SetDirectory(0)
                        _h_syst_dw.Sumw2()
                        _h_syst_dw.Scale(scale)
                        print "{:20} lnN {:1.3f}/{:1.3f}".format(
                            syst,
                            _h_syst_up.Integral()/hist.Integral() if hist.Integral() else 0,
                            _h_syst_dw.Integral()/hist.Integral() if hist.Integral() else 0,
                        )
                        if root_histos_syst.get(syst, None) is None:
                            root_histos_syst[syst] = {
                                "Up"   : _h_syst_up,
                                "Down" : _h_syst_dw
                            }
                        else:
                            root_histos_syst[syst]["Up"  ].Add(_h_syst_up)
                            root_histos_syst[syst]["Down"].Add(_h_syst_dw)
                                                    
                else:
                    print(colored(fn + " -> %i " %hist.Integral(), "yellow"))
                
                if hist_nom is None:
                    hist_nom = hist
                else:
                    hist_nom.Add(hist)
        
        print "+ process : ", procname, " nsyst : ", len(root_histos_syst.keys())
        
        for n, cnt in root_histos_syst.items():
            print "  -- syst : ", n
            check_nuisance(
                procname, n, channel, hist_nom,
                cnt["Up"], cnt["Down"]
            )
        
        
        
def main():
    drawing("catSignal-0jet" , lumi=41.50)
    drawing("catSignal-1jet" , lumi=41.50)
    drawing("cat3L" , lumi=41.50)
    drawing("cat4L" , lumi=41.50)
    drawing("catNRB", lumi=41.50)
    drawing("catTOP", lumi=41.50)
    drawing("catDY" , lumi=41.50)
    drawing("catEM" , lumi=41.50)
    drawing("njet"  , lumi=41.50)


if __name__=="__main__":
    main()
