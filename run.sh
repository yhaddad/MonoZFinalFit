python3 makeQuickCard.py --channel EE --stack=DMY1000Xd200,Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,DrellYanBinned,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200
python3 makeQuickCard.py --channel MM --stack=DMY1000Xd200,Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,DrellYanBinned,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200
python3 makeQuickCard.py --channel 3L --stack=WZ3lnu,Other3l,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200 -v emulatedMET
python3 makeQuickCard.py --channel 4L --stack=qqZZ4l,ggZZ4l,Other4l,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200 -v emulatedMET
python3 makeQuickCard.py --channel NRB --stack=Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200
python3 makeQuickCard.py --channel TOP --stack=Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,Data --input=config/merged_inputs.yaml --outdir=DMY1000Xd200
