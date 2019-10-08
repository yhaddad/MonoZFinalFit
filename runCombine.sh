#
for sig in ADD_MD_1_d_2
do
    echo " -- making data cards"
    python3 makeDataCard.py --channel catSignal-0jet catSignal-1jet --stack $sig ZZ WZ WW VVV TOP DY data --input=config/inputs-NanoAODv5-2017.yaml
    python3 makeDataCard.py --channel cat3L --stack $sig ZZ WZ WW VVV TOP DY data --input=config/inputs-NanoAODv5-2017.yaml
    python3 makeDataCard.py --channel cat4L --stack $sig ZZ WZ WW VVV TOP DY data --input=config/inputs-NanoAODv5-2017.yaml
    python3 makeDataCard.py --channel catEM --stack $sig ZZ WZ WW VVV TOP DY data --input=config/inputs-NanoAODv5-2017.yaml
    #python3 makeDataCard.py --channel catDY --stack $sig ZZ WZ WW VVV TOP DY data --input=config/inputs-NanoAODv5-2017.yaml
done
#ADD_MD_1_d_3 ADD_MD_1_d_4 ADD_MD_1_d_5 ADD_MD_1_d_6 ADD_MD_1_d_7 ADD_MD_2_d_2 ADD_MD_2_d_3 ADD_MD_2_d_4 ADD_MD_2_d_5 ADD_MD_2_d_6 ADD_MD_2_d_7 ADD_MD_3_d_2 ADD_MD_3_d_3 ADD_MD_3_d_4 ADD_MD_3_d_5 ADD_MD_3_d_6 ADD_MD_3_d_7
