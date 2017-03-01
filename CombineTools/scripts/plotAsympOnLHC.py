import ROOT
from ROOT import TMath
import math
import os
from math import floor
import CombineHarvester.CombineTools.plotting as plot
import argparse
import sys

# This script may be used to plot a toy distribution over the asymptotic prediction. The only
# required input is the path to the rootfile containing the toys (HypoTestResult class). This
# root file is usually produced by the HybridNewGrid method. It is possible to input multiple
# root files (without using an argument). See below (near line 50) for a list of all
# optional parameters.

# If no comparison with the asymptotic prediction is required, use at --no_asymp argument.
# Otherwise, it is necessary to manually input the result of the asymptotic calculation into
# this script (near line 70). The values q_mu and q_A are required.

def DrawCMSLogo(pad, cmsText, extraText):
    pad.cd()
    cmsTextSize=0.8
    cmsTextFont = 62
    extraTextFont = 52
    lumiTextOffset = 0.2
    extraOverCmsTextSize = 0.76
    l = pad.GetLeftMargin()
    t = pad.GetTopMargin()
    r = pad.GetRightMargin()
    b = pad.GetBottomMargin()
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)
    extraTextSize = extraOverCmsTextSize * cmsTextSize
    pad_ratio = (float(pad.GetWh()) * pad.GetAbsHNDC()) / \
        (float(pad.GetWw()) * pad.GetAbsWNDC())
    if (pad_ratio < 1.):
        pad_ratio = 1.
    latex.SetTextFont(cmsTextFont)
    latex.SetTextAlign(11)
    latex.SetTextSize(cmsTextSize * t * pad_ratio)
    latex.DrawLatex(l/4, 1 - t + lumiTextOffset * t, cmsText)
    posX_ = l/4 + 0.15 * (1 - l - r)
    posY_ = 1 - t + lumiTextOffset * t
    latex.SetTextFont(extraTextFont)
    latex.SetTextSize(extraTextSize * t * pad_ratio)
    latex.SetTextAlign(11)
    latex.DrawLatex(posX_, posY_, extraText)

#ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('files', help='Input root files containing HypoTestResult objects (no option prefix needed)', nargs='*')
parser.add_argument('--name', '-n', help='Appendix on the output name', default="")
parser.add_argument('--alt', help='Name for the alternative hypothesis', default="H_{1}")
parser.add_argument('--null', help='Name for the null hypothesis', default="H_{0}")
parser.add_argument('--bin_number', '-bins', help='Set the number of bins', default=120)
parser.add_argument('--expected', '-exp', help='Fix q_obs to a different value so CLb = 0.5', action='store_true')
parser.add_argument('--logx', '-logx', help='Draw x-axis in log scale', action='store_true')
parser.add_argument('--no_asymp', help='Show only toy distribution', action='store_true')
parser.add_argument('--fit_qa', help='Fit qA to the toy distribution of the null hypothesis', action='store_true')
parser.add_argument('--sb', help='Fit qA to the toy distribution of the alternative hypothesis instead', action='store_true')
parser.add_argument('--diff', help='Make a plot of the difference between Asymptotic and LHC toy based test statistic', action='store_true')
parser.add_argument('--display', '-d', help='Display plots right when they are done', action='store_true')
args = parser.parse_args()


AsympOnLHC = not args.no_asymp
args.bin_number = int(args.bin_number)
if AsympOnLHC:
  # Insert output from combine here #<----------------------------------------------
  # These values need to be taken from where it says 'At x = 1.000000:'
  qmu = 3.24655
  qA = 2.51344


  # TODO: Somehow write numbers to json, so they can be read more easily?

expclb=0.5 #0.025,0.16,0.5,0.84,0.975
results = []
for file in args.files:
  found_res = False
  f = ROOT.TFile(file)
  ROOT.gDirectory.cd('toys')
  for key in ROOT.gDirectory.GetListOfKeys():
    if ROOT.gROOT.GetClass(key.GetClassName()).InheritsFrom(ROOT.RooStats.HypoTestResult.Class()):
      results.append(ROOT.gDirectory.Get(key.GetName()))
      found_res = True
  f.Close()
  if not found_res:
    print '>> Warning, did not find a HypoTestResult object in file %s' % file
  if (len(results)) > 1:
    for r in results[1:]:
      results[0].Append(r)
  ntoys = min(results[0].GetNullDistribution().GetSize(), results[0].GetAltDistribution().GetSize())
  if ntoys == 0:
    print '>> Warning, HypoTestResult from file(s) %s does not contain any toy results, did something go wrong in your fits?' % '+'.join(args.files)
result=results[0]

alt_label = args.alt
null_label = args.null

filename = args.files[0]
aw = filename.find(".mA")
if aw != -1:
  aw += 4
  bw = aw
  while not filename[bw] == ".":
    bw += 1
  maval = filename[aw:bw]
else:
  maval = ""

aw = filename.find(".tanb")
if aw != -1:
  aw += 6
  bw = aw
  while not filename[bw] == ".":
    bw += 1
  tanbval = filename[aw:bw]
else:
  tanbval = ""

name = ''
if args.name != '': name = args.name
if maval != '' and tanbval != '':
  if name != '': name += '_'
  name += 'mA'+maval+'_'+'tanb'+tanbval
if name == '': name = 'plot'
if args.expected: name += '_exp'
if args.fit_qa: name += '_fit'

null_vals = [toy * 2. for toy in result.GetNullDistribution().GetSamplingDistribution()]
alt_vals = [toy * 2. for toy in result.GetAltDistribution().GetSamplingDistribution()]
val_obs = result.GetTestStatisticData() * 2.

if args.expected:
  null_vals.sort()
  val_obs = null_vals[int(min(floor((1-expclb) * len(null_vals) +0.5), len(null_vals)-1))]#null_vals[len(null_vals)/2]
  result.SetTestStatisticData(val_obs/2)

if len(null_vals) == 0 or len(alt_vals) == 0:
  print '>> Error in PlotTestStat for %s, null and/or alt distributions are empty'
  exit()
plot.ModTDRStyle()
canv = ROOT.TCanvas(name, name)
pads = plot.TwoPadSplit(0.8, 0, 0)
pads[1].cd()
min_val = min(min(alt_vals), min(null_vals))
max_val = max(max(alt_vals), max(null_vals))
#min_plot_range = min_val - 0.05 * (max_val - min_val)
min_plot_range = 0.
pads[1].SetLogy(True)
if args.logx:
  pads[1].SetLogx(True)
max_plot_range = max_val + 0.05 * (max_val - min_val)

if AsympOnLHC:
  if args.expected:
    eN = ROOT.Math.normal_quantile(0.5, 1.0)
    qmu = qA

  TotalToysSB=result.GetAltDistribution().GetSize()
  TotalToysB=result.GetNullDistribution().GetSize()

  # The rate by how much the asymptotic distribution needs to be scaled depends on the bin width, so the maximum plot range.
  # But the maximum plot range also depends on how high the asymptotic distribution is.
  # It's enough to go through this iteratively twice.
  for i in range(2):
    test1 = ROOT.TF1("f1","[0]/(sqrt(8*TMath::Pi()*[1]))*(TMath::Exp(-1/(8*[1])*(x+[1])*(x+[1])))",qA,max_plot_range*9999)
    test2 = ROOT.TF1("f2","[0]/(sqrt(8*TMath::Pi()*[1]))*(TMath::Exp(-1/(8*[1])*(x-[1])*(x-[1])))",qA,max_plot_range*9999)
    test1.SetParameter(0,TotalToysSB)
    test1.SetParameter(1,qA)
    test2.SetParameter(0,TotalToysB)
    test2.SetParameter(1,qA)
    mult1 = 1.0
    while test1.Eval(mult1*qA) > 0.8 :
      mult1 +=0.1
    mult2 = 1
    while test2.Eval(mult2*qA) > 0.8:
      mult2 +=0.1
    mult = max(mult1, mult2)
    if mult*qA > max_val: max_plot_range = mult*qA + 0.05 * (max_val - min_val)
    TotalToysSB=result.GetAltDistribution().GetSize()*(max_plot_range-min_plot_range)/args.bin_number
    TotalToysB=result.GetNullDistribution().GetSize()*(max_plot_range-min_plot_range)/args.bin_number

hist_null = ROOT.TH1F('null', 'null', args.bin_number, min_plot_range, max_plot_range)
hist_alt = ROOT.TH1F('alt', 'alt', args.bin_number, min_plot_range, max_plot_range)
for val in null_vals: hist_null.Fill(val)
for val in alt_vals: hist_alt.Fill(val)
hist_alt.SetLineColor(ROOT.TColor.GetColor(4, 4, 255))
hist_alt.SetFillColor(plot.CreateTransparentColor(ROOT.TColor.GetColor(4, 4, 255), 0.4))
hist_alt.GetXaxis().SetTitle('q')
hist_alt.GetYaxis().SetTitle('Toys')
hist_alt.GetYaxis().SetTitleOffset(1.0)
hist_alt.SetMinimum(0.8)
hist_alt.Draw()
hist_null.SetLineColor(ROOT.TColor.GetColor(252, 86, 11))
hist_null.SetFillColor(plot.CreateTransparentColor(ROOT.TColor.GetColor(254, 195, 40), 0.4))
hist_null.Draw('SAME')
histmax = hist_alt.GetMaximum()
obs = ROOT.TArrow(val_obs, 0, val_obs, histmax * 0.01, 0.05 , '<-|')
obs.SetLineColor(ROOT.kRed)
obs.SetLineWidth(3)
obs.Draw()
#plot.FixTopRange(pads[1], plot.GetPadYMax(pads[1]), 0.25)
if AsympOnLHC:
  leg = ROOT.TLegend(0.68-ROOT.gPad.GetRightMargin(), 0.72-ROOT.gPad.GetTopMargin(), 0.99-ROOT.gPad.GetRightMargin(), 0.99-ROOT.gPad.GetTopMargin(), '', 'NBNDC')
else:
  leg = ROOT.TLegend(0.68-ROOT.gPad.GetRightMargin(), 0.85-ROOT.gPad.GetTopMargin(), 0.99-ROOT.gPad.GetRightMargin(), 0.99-ROOT.gPad.GetTopMargin(), '', 'NBNDC')
leg.AddEntry(hist_alt, alt_label, 'F')
leg.AddEntry(hist_null, null_label, 'F')
if args.expected:
  leg.AddEntry(obs, 'Expected', 'L')
else:
  leg.AddEntry(obs, 'Observed', 'L')
pads[0].cd()
if args.fit_qa:
  pt_l1 = ROOT.TPaveText(0.23, 0.66, 0.33, 0.78, 'NDCNB')
else:
  pt_l1 = ROOT.TPaveText(0.23, 0.72, 0.33, 0.78, 'NDCNB')
pt_l1.AddText('Model:')
pt_l1.AddText('Toys:')
if args.fit_qa:
  pt_l1.AddText('Old q_{A}:')
  pt_l1.AddText('Fit q_{A}:')
plot.Set(pt_l1, TextAlign=11, TextFont=62, BorderSize=0)
pt_l1.Draw()
pt_la = ROOT.TPaveText(0.20, 0.80, 0.30, 0.99, 'NDCNB')
pt_la.AddText('')
pt_la.AddText('CL_{s+b} :')
pt_la.AddText('CL_{b} :')
pt_la.AddText('CL_{s} :')
if args.expected and AsympOnLHC:
  pt_la.AddText('q_{exp} :')
else:
  pt_la.AddText('q_{obs} :')
plot.Set(pt_la, TextAlign=11, TextFont=62, BorderSize=0)
pt_la.Draw()
if AsympOnLHC:
  pt_t1 = ROOT.TPaveText(0.33, 0.95, 0.52, 0.99, 'NDCNB')
  pt_t2 = ROOT.TPaveText(0.55, 0.95, 0.74, 0.99, 'NDCNB')
  pt_t1.AddText('Toy based')
  pt_t2.AddText('Asymptotic')
  plot.Set(pt_t1, TextAlign=11, TextFont=62, BorderSize=0)
  pt_t1.Draw()
  plot.Set(pt_t2, TextAlign=11, TextFont=62, BorderSize=0)
  pt_t2.Draw()
if args.fit_qa and AsympOnLHC:
  pt_r1 = ROOT.TPaveText(0.32, 0.66, 0.62, 0.78, 'NDCNB')
else:
  pt_r1 = ROOT.TPaveText(0.32, 0.72, 0.62, 0.78, 'NDCNB')
pt_r1.AddText('%s [%s = %s, %s = %s]' % ('m_{h}^{mod+}', 'mA', maval, 'tanb', tanbval))
pt_r1.AddText('%i (%s) + %i (%s)' % (result.GetNullDistribution().GetSize(), null_label, result.GetAltDistribution().GetSize(), alt_label))
if not args.fit_qa or not AsympOnLHC:
  plot.Set(pt_r1, TextAlign=11, TextFont=42, BorderSize=0)
  pt_r1.Draw()
pt_b1 = ROOT.TPaveText(0.33, 0.79, 0.52, 0.95, 'NDCNB')
pt_b1.AddText('%.3f #pm %.3f' % (result.CLsplusb(), result.CLsplusbError()))
pt_b1.AddText('%.3f #pm %.3f' % (result.CLb(), result.CLbError()))
pt_b1.AddText('%.3f #pm %.3f' % (result.CLs(), result.CLsError()))
pt_b1.AddText('%.5f' % (val_obs))
plot.Set(pt_b1, TextAlign=11, TextFont=42, BorderSize=0)
pt_b1.Draw()
if AsympOnLHC:
  pt_b2 = ROOT.TPaveText(0.55, 0.79, 0.74, 0.95, 'NDCNB')
#DrawCMSLogo(pads[0], 'CMS', "(private work)")

if AsympOnLHC:
  deltarange=0.00000000001#max_plot_range/args.bin_number
  f1 = ROOT.TF1("f1","(x<=[2])*0.5*[0]+(x>[2])*(x<=[1])*[0]/(sqrt(8*TMath::Pi()*x))*(TMath::Exp(-1/2*x)) + (x>[1])*[0]/(sqrt(8*TMath::Pi()*[1]))*(TMath::Exp(-1/(8*[1])*(x+[1])*(x+[1])))",0,max_plot_range)
  f1.FixParameter(0,TotalToysSB)
  f1.SetParameter(1,qA)
  f1.FixParameter(2,deltarange)

  f2 = ROOT.TF1("f2","(x<=[2])*[3]*[0]+(x>[2])*(x<=[1])*[0]/(sqrt(8*TMath::Pi()*x))*(TMath::Exp(-1/2*(sqrt(x)-sqrt([1]))*(sqrt(x)-sqrt([1])))) + (x>[1])*[0]/(sqrt(8*TMath::Pi()*[1]))*(TMath::Exp(-1/(8*[1])*(x-[1])*(x-[1])))",0,max_plot_range)

  f2.FixParameter(0,TotalToysB)
  f2.SetParameter(1,qA)
  f2.FixParameter(2,deltarange)
  f2.FixParameter(3,ROOT.Math.normal_cdf(math.sqrt(qA),1))

  if args.fit_qa:
    pt_r1.AddText('%.5f' % (qA))
    if args.sb:
      hist_alt.Fit(f2, "QR0")#,"",max_plot_range/args.bin_number+0.01,max_plot_range)
    else:
      hist_null.Fit(f2, "QR0","",max_plot_range/args.bin_number+0.01,max_plot_range)
    qA = f2.GetParameter(1)
    f1.SetParameter(1,qA)
    pt_r1.AddText('%.5f' % (qA))
    plot.Set(pt_r1, TextAlign=11, TextFont=42, BorderSize=0)
    pt_r1.Draw()
    if args.expected: qmu = qA

pads[1].cd()
pads[1].GetFrame().Draw()
pads[1].RedrawAxis()

if AsympOnLHC:
  #if qmu==0: qmu=0.0000000000001
  if qmu==0:
    asy_sb=0.5
    asy_b=ROOT.Math.normal_cdf(math.sqrt(qA),1)
  else:
    asy_sb=f1.Integral(qmu,max_plot_range)/TotalToysSB
    asy_b=f2.Integral(qmu,max_plot_range)/TotalToysB
  #print "total sb: "+str(f1.Integral(0,max_plot_range)/TotalToysSB)
  #print "total b: "+str(f2.Integral(0,max_plot_range)/TotalToysSB)
  pads[0].cd()
  pt_b2.AddText('%.3f' % (asy_sb))
  pt_b2.AddText('%.3f' % (asy_b))
  pt_b2.AddText('%.3f' % (asy_sb/asy_b))
  pt_b2.AddText('%.5f' % (qmu))
  plot.Set(pt_b2, TextAlign=11, TextFont=42, BorderSize=0)
  pt_b2.Draw()
  pads[1].cd()

  hist_alt.SetMaximum(histmax*2)
  if args.logx: hist_alt.GetXaxis().SetRange(hist_alt.GetXaxis().FindBin((max_plot_range-min_plot_range)/args.bin_number *0.9),hist_alt.GetNbinsX())

  obs2 = ROOT.TArrow(qmu, 0, qmu, histmax * 0.015, 0.05 , '<-|')
  obs2.SetLineColor(ROOT.kGreen+2)
  obs2.SetLineWidth(3)
  obs2.Draw()
  leg.AddEntry(f1, alt_label+' Asymptotic', 'L')
  leg.AddEntry(f2, null_label+' Asymptotic', 'L')
  if args.expected:
    leg.AddEntry(obs2, 'Asymp. Expected', 'L')
  else:
    leg.AddEntry(obs2, 'Asymp. Observed', 'L')

  f1.SetLineWidth(3)
  f1.SetLineColor(ROOT.kBlue)
  f1.Draw("same")
  f2.SetLineWidth(3)
  f2.SetLineColor(ROOT.kOrange+7)
  f2.Draw("same")
leg.Draw()
canv.SaveAs("AsympOnLHC_"+name+".png")
if args.display: os.system("display AsympOnLHC_"+name+".png &")

if args.diff and AsympOnLHC:
  sbdiff = ROOT.TH1F('sbdiff', 'sbdiff', args.bin_number, min_plot_range, max_plot_range)
  bdiff = ROOT.TH1F('bdiff', 'bdiff', args.bin_number, min_plot_range, max_plot_range)
  sbdiffone = f1.Eval(hist_alt.GetBinCenter(1))-hist_alt.GetBinContent(1)
  bdiffone = f2.Eval(hist_null.GetBinCenter(1))-hist_null.GetBinContent(1)
  sbdifftotal = sbdiffone
  bdifftotal = bdiffone
  for i in xrange(2,args.bin_number+1):
    sbdiffval = f1.Eval(hist_alt.GetBinCenter(i))-hist_alt.GetBinContent(i)
    bdiffval = f2.Eval(hist_null.GetBinCenter(i))-hist_null.GetBinContent(i)
    sbdifftotal += sbdiffval
    bdifftotal += bdiffval
    sbdiff.SetBinContent(i,sbdiffval)
    bdiff.SetBinContent(i,bdiffval)
  maxdiff = max(max(sbdiff.GetMaximum(),bdiff.GetMaximum()),-1*min(sbdiff.GetMinimum(),bdiff.GetMinimum()))
  sbdiff.SetMaximum(maxdiff)
  bdiff.SetMaximum(maxdiff)
  sbdiff.SetMinimum(-1*maxdiff)
  bdiff.SetMinimum(-1*maxdiff)
  canv2 = ROOT.TCanvas(name+'_diff', name+'_diff')
  pads2 = plot.TwoPadSplit(0.8, 0, 0)
  pads2[1].cd()
  sbdiff.SetLineColor(ROOT.TColor.GetColor(4, 4, 255))
  sbdiff.SetFillColor(plot.CreateTransparentColor(ROOT.TColor.GetColor(4, 4, 255), 0.4))
  sbdiff.GetXaxis().SetTitle('-2 #times ln(^{}L_{%s}/^{}L_{%s})' % (alt_label, null_label))
  sbdiff.GetYaxis().SetTitle('Diff.  Asymp. - Toys')
  bdiff.SetLineColor(ROOT.TColor.GetColor(252, 86, 11))
  bdiff.SetFillColor(plot.CreateTransparentColor(ROOT.TColor.GetColor(254, 195, 40), 0.4))
  sbdiff.Draw()
  bdiff.Draw("same")

  pads2[0].cd()
  leg2 = ROOT.TLegend(0.82-ROOT.gPad.GetRightMargin(), 0.76-ROOT.gPad.GetTopMargin(), 0.98-ROOT.gPad.GetRightMargin(), 0.83-ROOT.gPad.GetTopMargin(), '', 'NBNDC')
  leg2.AddEntry(sbdiff, alt_label, 'F')
  leg2.AddEntry(bdiff, null_label, 'F')
  leg2.Draw()
  pt_diff1 = ROOT.TPaveText(0.15, 0.82, 0.52, 0.95, 'NDCNB')
  pt_diff1.AddText(alt_label+'-diff. at q=0: %.2f ' % (sbdiffone))
  pt_diff1.AddText(null_label+'-diff. at q=0: %.2f ' % (bdiffone))
  pt_diff1.Draw()
  pt_diff2 = ROOT.TPaveText(0.58, 0.82, 0.95, 0.95, 'NDCNB')
  pt_diff2.AddText('Total '+alt_label+'-diff.: %.2f ' % (sbdifftotal))
  pt_diff2.AddText('Total '+null_label+'-diff.: %.2f ' % (bdifftotal))
  pt_diff2.Draw()
  canv2.SaveAs("AsympOnLHCDiff_"+name+".png")
  if args.display: os.system("display AsympOnLHCDiff_"+name+".png &")
