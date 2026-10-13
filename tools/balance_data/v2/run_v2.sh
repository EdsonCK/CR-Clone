#!/bin/sh
# v2 balance run: ROUNDS rounds of (full games -> engagement tune -> combine),
# then a final full-game measurement of the result.
cd /home/user/CR-Clone
D=tools/balance_data/v2
ROUNDS=${ROUNDS:-3}
export SDL_VIDEODRIVER=dummy PROCS=4
[ -f $D/snap0.json ] || echo '{}' > $D/snap0.json
# round 0's full-game baseline may still be running in the background
while [ ! -f $D/full0.json ]; do sleep 20; done
R=0
while [ $R -lt $ROUNDS ]; do
  N=$((R + 1))
  [ -f $D/full$R.json ] || SEED0=$((R * 100000)) python3 tools/fullgame.py $D/full$R.json $D/snap$R.json 12000 > $D/full$R.log 2>&1
  [ -f $D/tune$R.json ] || SPELL_TARGET=-0.30 python3 tools/balance.py tune $D/tune$R.json $D/snap$R.json > $D/tune$R.log 2>&1
  python3 tools/balance_v2.py combine $D/snap$R.json $D/tune$R.json $D/full$R.json $D/snap$N.json > $D/combine$R.log 2>&1
  echo "round $R done" >> $D/progress.log
  R=$N
done
SEED0=900000 python3 tools/fullgame.py $D/full$R.json $D/snap$R.json 12000 > $D/full$R.log 2>&1
echo "final done" >> $D/progress.log
