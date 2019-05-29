for sig in DMY1000Xd10 DMY1000Xd100 DMY1000Xd200 DMY1000Xd300 DMY1000Xd400 DMY1000Xd510 DMY1250Xd1 DMY1500Xd1 DMY1750Xd1 DMY2000Xd1 DMY250Xd1 DMY500Xd1:
do
  python3 makeQuickCard.py --channel EE --stack=$sig,Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,DrellYanBinned,Data --input=config/merged_inputs.yaml --outdir=$sig
  python3 makeQuickCard.py --channel MM --stack=$sig,Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,DrellYanBinned,Data --input=config/merged_inputs.yaml --outdir=$sig
  python3 makeQuickCard.py --channel 3L --stack=WZ3lnu,Other3l,Data --input=config/merged_inputs.yaml --outdir=$sig -v emulatedMET
  python3 makeQuickCard.py --channel 4L --stack=qqZZ4l,ggZZ4l,Other4l,Data --input=config/merged_inputs.yaml --outdir=$sig -v emulatedMET
  python3 makeQuickCard.py --channel NRB --stack=Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,Data --input=config/merged_inputs.yaml --outdir=$sig
  python3 makeQuickCard.py --channel TOP --stack=Nonresonant,qqZZ2l2nu,ggZZ2l2nu,WZ3lnu,Other,Data --input=config/merged_inputs.yaml --outdir=$sig

  rm -rf $sig/card_*_bin40to50
  rm -rf $sig/card_*_bin50to75
  rm -rf $sig/card_*_bin75to100
  rm -rf $sig/card_*_bin0to40
  rm -rf $sig/card_*_bin40to45
  rm -rf $sig/card_*_bin45to50
done
