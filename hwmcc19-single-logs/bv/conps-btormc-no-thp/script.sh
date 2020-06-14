#!/bin/sh
#SBATCH -e /dev/null
#SBATCH -o /dev/null
#SBATCH -c 32
#SBATCH -a 1-317
#SBATCH -D /home/mathias/hwmcc19/hwmcc19-final-runs/20191015-conps-btormc-no-thp

benchmarks="/home/mathias/hwmcc19/hwmcc19-final-runs/20191015-conps-btormc-no-thp/btor_bv_hwmcc19/benchmarks"

# pick benchmark file from list of benchmarks
prefix="/home/mathias/hwmcc19/benchmarks-single/btor2/"
BENCHMARK="$(sed ${SLURM_ARRAY_TASK_ID}'q;d' $benchmarks)"
out="$(echo "${BENCHMARK#$prefix}" | sed -e 's,/,-,g')"
# set stdout log file
log="/home/mathias/hwmcc19/hwmcc19-final-runs/20191015-conps-btormc-no-thp/btor_bv_hwmcc19/${out}.log"
# set stderr log file
err="/home/mathias/hwmcc19/hwmcc19-final-runs/20191015-conps-btormc-no-thp/btor_bv_hwmcc19/${out}.err"

export BENCHMARK
(
  RUNLIM_BIN="/home/mathias/bin/runlim"
  RUNLIM_OPTS="--real-time-limit=3600 --space-limit=120000"
  SOLVER_BIN="./run-conps-btormc-no-thp.sh"
  SOLVER_OPTS=""
  SCRAMBLER=""

  echo "c host: $(hostname)"
  echo "c start: $(date)"
  echo "c arrayjobid: ${SLURM_ARRAY_JOB_ID}"
  echo "c jobid: ${SLURM_JOB_ID}"
  echo "c benchmark: $BENCHMARK"
  echo "c solver: $SOLVER_BIN"
  echo "c solver options: $SOLVER_OPTS"

  PRIVATE_TMP="/tmp/slurm.${SLURM_JOB_ID:=0}.${SLURM_RESTART_COUNT:=0}"
  mkdir "${PRIVATE_TMP}" || exit 1
  echo "c tmpdir: ${PRIVATE_TMP}"

  filename="$(basename $BENCHMARK)"
  extension="${filename##*.}"
  [ -n "$extension" ] && extension=".$extension"
  INPUT_FILE="$(mktemp --suffix="$extension" \
                        --tmpdir="${PRIVATE_TMP}" XXXXXXXX)"

  # scramble benchmark if scrambler is given
  if [ -e "$SCRAMBLER" ]; then
    $SCRAMBLER "$BENCHMARK"  > "$INPUT_FILE"
  else
    cp "$BENCHMARK" "$INPUT_FILE" || exit 1
  fi

  export INPUT_FILE="/tmp/$(basename "$INPUT_FILE")"
  export PRIVATE_TMP
  export RUNLIM_BIN
  export RUNLIM_OPTS
  export SOLVER_BIN
  export SOLVER_OPTS

  /home/mathias/hwmcc19/bwrap --dev-bind / / --bind ${PRIVATE_TMP} /tmp   	$RUNLIM_BIN $RUNLIM_OPTS "$SOLVER_BIN" $SOLVER_OPTS "$INPUT_FILE"

#  # Create private /tmp directory for each job
#  unshare -m --map-root-user /bin/bash -c '
#  (
#    mount --bind "${PRIVATE_TMP}" /tmp
#
#    $RUNLIM_BIN $RUNLIM_OPTS "$SOLVER_BIN" $SOLVER_OPTS "$INPUT_FILE"
#  )'

  if [ -d "${PRIVATE_TMP}" ]; then
    rm -rf "${PRIVATE_TMP}"
  fi

  echo "c done"

) > "$log" 2> "$err"
