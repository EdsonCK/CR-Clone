#!/bin/sh
cd /tmp/claude-0/-home-user-CR-Clone/9e04abf9-ccf3-56ef-a276-a1c3aa096e15/scratchpad/bal_v3
D=tools/balance_data/v3
export SDL_VIDEODRIVER=dummy PROCS=4
for R in 3 4; do
  N=$((R + 1))
  SEED0=$((R * 100000)) python3 tools/fullgame.py $D/full$R.json $D/snap$R.json 12000 > $D/full$R.log 2>&1
  SPELL_TARGET=-0.30 python3 tools/balance.py tune $D/tune$R.json $D/snap$R.json > $D/tune$R.log 2>&1
  python3 tools/balance_v2.py combine $D/snap$R.json $D/tune$R.json $D/full$R.json $D/snap$N.json > $D/combine$R.log 2>&1
  echo "round $R done" >> $D/progress.log
done
SEED0=900000 python3 tools/fullgame.py $D/full5.json $D/snap5.json 12000 > $D/full5.log 2>&1
echo "final done" >> $D/progress.log
