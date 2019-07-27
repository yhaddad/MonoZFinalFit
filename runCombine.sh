# ADD_MD_1_d_4 ADD_MD_1_d_5 ADD_MD_1_d_6 ADD_MD_1_d_7 ADD_MD_2_d_2 ADD_MD_2_d_3 ADD_MD_2_d_4 ADD_MD_2_d_5 ADD_MD_2_d_6 ADD_MD_2_d_7 ADD_MD_3_d_2 ADD_MD_3_d_3 ADD_MD_3_d_4 ADD_MD_3_d_5 ADD_MD_3_d_6 ADD_MD_3_d_7
for sig in ADD_MD_1_d_2 ADD_MD_1_d_3
do
    echo " -- making data cards"
    python makeQuickCard.py --channel catSignal-0jet --stack=$sig,ZZ,WZ,WW,VVV,TOP,DY,Data --input=config/inputs-NanoAODv5-2017.yaml --outdir=fitroom/$sig
    python makeQuickCard.py --channel catSignal-1jet --stack=$sig,ZZ,WZ,WW,VVV,TOP,DY,Data --input=config/inputs-NanoAODv5-2017.yaml --outdir=fitroom/$sig
    python makeQuickCard.py --channel cat3L          --stack=$sig,ZZ,WZ,WW,VVV,TOP,DY,Data --input=config/inputs-NanoAODv5-2017.yaml --outdir=fitroom/$sig
    python makeQuickCard.py --channel cat4L          --stack=$sig,ZZ,WZ,WW,VVV,TOP,DY,Data --input=config/inputs-NanoAODv5-2017.yaml --outdir=fitroom/$sig
    python makeQuickCard.py --channel catEM          --stack=$sig,ZZ,WZ,WW,VVV,TOP,DY,Data --input=config/inputs-NanoAODv5-2017.yaml --outdir=fitroom/$sig

    echo " -- prepare combine cards -- "
    updir=$PWD
    cd fitroom/
    combineCards.py -S $sig/card_* > combined_$sig.dat
    text2workspace.py -m 125 combined_$sig.dat --channel-masks

    echo " -- validate datacards -- "
    ValidateDatacards.py combined_$sig.dat.root

    echo " -- running limits --"
    combine -M AsymptoticLimits combined_$sig.dat.root -m 125 --run blind | tee logs/combine-fit-$sig.txt

    mv higgsCombineTest.AsymptoticLimits.mH125.root higgsCombineTest.AsymptoticLimits.$sig.root
    cd $updir
done
