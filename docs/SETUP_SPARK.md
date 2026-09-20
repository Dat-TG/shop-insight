# Setting up Spark — from zero, on your own

For Khang, Nguyen and Tin, and for anyone who reinstalls later. You do not need to
have used Spark or Java before. Follow the steps in order. Every step ends with a
**Check** line: do not move on until your output matches it.

**Vietnamese version, with every step and every file explained for Spark beginners:**
[SPARK_GUIDE_VI.md](SPARK_GUIDE_VI.md). Both describe the same procedure; change a command
in one, change it in the other.

**At the end**, `python processing/kata.py` prints `KATA OK`. Post its full output
in the group chat. That post is how the rest of us know your machine is ready.

**Time:** about 30 minutes of installing, plus the 9 GB data download.
**Disk:** about 12 GB free (9 GB CSV, about 1.7 GB for Java, PySpark and pip's download
cache, plus the project's own data later).
**Stuck for more than 48 hours?** Raise a red flag in the group (PLAN.md). Don't wait for
Wednesday.

---

## 1. Platform: Ubuntu 26.04, native or in WSL2

Every command below is for **Ubuntu 26.04**, either installed directly or running
inside **WSL2** on Windows. Python 3.14 is the only Python that Ubuntu 26.04 ships,
and the whole toolchain is pinned around it (SYSTEM_DESIGN.md section 11.1).

**On Windows, use WSL2, not Windows itself.** Spark on native Windows needs
`winutils.exe` and a `HADOOP_HOME`, and it breaks in ways nobody in the team can debug.
In PowerShell:

```powershell
wsl --list --online              # find the Ubuntu 26.04 entry in the NAME column
wsl --install -d <that name>     # then open "Ubuntu" from the Start menu and create a user
```

Inside Ubuntu, clone the repo **into your Linux home directory**, not under `/mnt/c/`.
Files under `/mnt/c/` are read through a slow bridge, and a 9 GB CSV there reads
several times slower. Dat has to add you as a collaborator on GitHub first.

```bash
cd ~
git clone https://github.com/Dat-TG/shop-insight.git
cd shop-insight
```

**Check:** `grep VERSION_ID /etc/os-release` prints `VERSION_ID="26.04"`, and `pwd`
prints `/home/<you>/shop-insight`.

## 2. Java 21 and the Python venv module

Spark runs inside a Java virtual machine (JVM). Spark 4.x needs Java 17 or newer. The
team pins **OpenJDK 21** so that all four machines run the same thing.

Ubuntu ships Python 3.14 **without** the module that creates virtual environments, so
install that too:

```bash
sudo apt update
sudo apt install -y openjdk-21-jdk-headless python3.14-venv unzip
```

**Check:** `java -version` prints a first line starting with `openjdk version "21.`

## 3. JAVA_HOME

PySpark looks for Java through the `JAVA_HOME` variable. This line works out where apt
put Java and saves it in `~/.bashrc`, so every new terminal has it:

```bash
echo 'export JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"' >> ~/.bashrc
source ~/.bashrc
```

**Check:** `echo $JAVA_HOME` prints `/usr/lib/jvm/java-21-openjdk-amd64` (on an ARM
machine: `-arm64`), and `$JAVA_HOME/bin/java -version` prints version 21 again.

If you had an older Java installed before, run `sudo update-alternatives --config java`,
pick the Java 21 entry, then open a new terminal.

## 4. Virtual environment and PySpark

A virtual environment (`.venv/`) keeps the project's Python packages apart from the
system's. It is gitignored: each person creates their own.

```bash
cd ~/shop-insight
python3.14 -m venv .venv
source .venv/bin/activate          # your prompt now starts with (.venv)
pip install -r requirements.txt    # PySpark is a 434 MB download and is built locally: a few minutes
```

**Activate the venv in every new terminal** before running anything in this repo:
`source .venv/bin/activate`.

**Check:** `python -c "import pyspark; print(pyspark.__version__)"` prints `4.1.3`.

## 5. Why exactly pyspark==4.1.3

`requirements.txt` pins `pyspark==4.1.3`. Keep that exact version, and never run
`pip install pyspark` without a version or `pip install -U`. A plain
`pip install pyspark` today installs 4.2.0, and an old tutorial will tell you to install 3.5.

**PySpark 3.5.x crashes the whole Python process (a segfault) on Python 3.14.**

- PySpark 3.5 ships its own copy of cloudpickle 2.x, the library that turns Python
  functions into bytes Spark can send around.
- That old cloudpickle calls `pickle._getattribute`, an internal Python function that
  changed in Python 3.14.
- cloudpickle serialises every function passed to `foreachBatch`, and `foreachBatch` is
  how this project writes to Cassandra (CLAUDE.md hard rule 2).

So a wrong version installs cleanly and runs every batch script. It only crashes in W40,
on the streaming Cassandra writes, when it is too late to find out why. 4.1.3 does not
have the problem.

## 6. Spark configuration, and two traps

The repo commits Spark's settings in [`conf/spark-defaults.conf`](../conf/spark-defaults.conf):

| Setting | Why |
|---|---|
| `spark.driver.memory 6g` | The Java heap Spark gets. Without it the heap is 1 GB and the bigger jobs run out of memory |
| `spark.sql.session.timeZone UTC` | Makes every machine read and write times in UTC, whatever its own clock says. Without it, a laptop set to Vietnam time (UTC+7) files the events of 30 Nov after 17:00 UTC under 1 Dec, and bronze gets 31 date folders instead of 30 |

Spark reads this file only if the `SPARK_CONF_DIR` variable points at `conf/` **before
the JVM starts**. You don't have to set anything: every script in the repo does it in its
first lines, before it creates a SparkSession.

```python
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))                      # lets the script import processing.schema
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # must come before the first SparkSession
```

When you write a new Spark script, copy those three lines to the top.

**Trap 1: memory set in code works only sometimes.** Many tutorials show this:

```python
# DON'T: works in some cases, silently does nothing in others
SparkSession.builder.config("spark.driver.memory", "6g").getOrCreate()
```

A JVM's heap size is fixed when the JVM starts, and PySpark (through a library called
py4j) starts the JVM only once per Python process. So this line works **only if this
builder is what starts the JVM**. If a JVM is already running, the setting is ignored.
That is the case in the `pyspark` shell, in a Jupyter notebook after the first session,
and in any script that created a session earlier. Measured on PySpark 4.1.3:

| Situation | Real heap | What `getConf()` reports |
|---|---|---|
| First session in `python script.py` | 6.0 GiB (it worked) | `6g` |
| `getOrCreate()` while a session is running | 1.0 GiB | unset, plus a `WARN ... only runtime SQL configurations will take effect` |
| New session after `spark.stop()`, same process | **1.0 GiB** | **`6g`**: the config claims a heap you don't have |

The last row is the dangerous one: no error, no warning, the config looks right, and the
job fails with `OutOfMemoryError` an hour later. So put memory settings in
`conf/spark-defaults.conf`, and only there. That works in every case above, which is why
`kata.py` prints the heap the JVM really has, not the config value.

**Trap 2: `spark.executor.memory` does nothing here.** We run Spark with
`master("local[*]")`: one JVM on your laptop, using every CPU core. In that mode the
driver *is* the executor, so executor settings have nothing to apply to. Don't set it and
don't tune it. Only `spark.driver.memory` counts.

**Check:** step 8 prints both settings from the running JVM.

## 7. Download the data

The dataset is REES46 "eCommerce behavior data from multi category store" on Kaggle:
<https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store>.
We only need `2019-Nov.csv`. `data/` is gitignored, so each person downloads it
themselves.

**Browser (simplest).** Sign in to Kaggle, download `2019-Nov.csv` from the dataset page,
then copy it into WSL. If Kaggle gives you a `.zip`, unzip it first.

```bash
cp /mnt/c/Users/<your Windows user>/Downloads/2019-Nov.csv ~/shop-insight/data/raw/
```

**Command line.** Needs a Kaggle API token in `~/.kaggle/kaggle.json` and the Kaggle CLI.
`pip install kaggle` inside your venv is fine, but don't add it to `requirements.txt`.

```bash
kaggle datasets download -d mkechinov/ecommerce-behavior-data-from-multi-category-store -f 2019-Nov.csv -p data/raw/
unzip -o data/raw/2019-Nov.csv.zip -d data/raw/ && rm data/raw/2019-Nov.csv.zip
```

**Check:** `wc -c data/raw/2019-Nov.csv` prints `9006762395`. A smaller number means the
download was cut off: download it again.

## 8. Run the kata

```bash
source .venv/bin/activate
python processing/kata.py
```

It reads the first 100,000 rows of the CSV with Spark and counts them by event type. It
takes 10 seconds on a 20-core machine, up to a minute or so on a small laptop. Spark's own log lines (`WARN ...`) and a `[Stage 0: ...]`
progress bar are normal.

**Check:** the output ends like this. The numbers must match exactly.

```
Python 3.14.4 | Spark 4.1.3 | Java 21.0.12
Driver heap: 6.0 GiB (expect 6.0; about 1.0 means conf/spark-defaults.conf was not read)
Time zone:   UTC (expect UTC)
Events from: 2019-11-01 00:00:00 to 2019-11-01 03:52:45 (expect 2019-11-01 00:00:00 to 2019-11-01 03:52:45)

view                97,489
cart                 1,089
remove_from_cart         0
purchase             1,422
KATA OK
```

`remove_from_cart` is 0 on purpose: the November file has no such events.
The Python and Java patch versions may differ slightly (`3.14.x`, `21.0.x`).

**Post the whole output in the group chat.** That completes your W38 setup.

## 9. When something goes wrong

Find the text you see in the first column. Spark prints long Java stack traces: search
them for the line that starts with `Caused by:` or `Exception`.

### Any machine

| You see | Cause | Fix |
|---|---|---|
| `JAVA_HOME is not set`, or `Java gateway process exited before sending its port number` | Java is not installed, or `JAVA_HOME` is wrong or not loaded | Steps 2 and 3. Open a new terminal, then `echo $JAVA_HOME` |
| `UnsupportedClassVersionError ... class file version 61.0` | An old Java (8 or 11) runs first | `sudo update-alternatives --config java`, pick 21, open a new terminal |
| `The virtual environment was not created successfully because ensurepip is not available` | `python3.14-venv` is missing: Ubuntu does not install it by default | `sudo apt install -y python3.14-venv`, then `rm -rf .venv` and step 4 again |
| `error: externally-managed-environment` | You ran `pip` outside the venv | `source .venv/bin/activate`, then run pip again |
| `No module named 'pyspark'` | The venv is not active in this terminal | `source .venv/bin/activate` |
| `Segmentation fault`, or `Fatal Python error` | A PySpark other than 4.1.3 is installed | `pip install -r requirements.txt`, then re-run the step 4 check |
| `Python in worker has different version` | Spark started a Python other than the venv's | Activate the venv. If it persists: `export PYSPARK_PYTHON="$(which python)"` |
| `Malformed records are detected in record parsing. Parse Mode: FAILFAST` | The CSV is damaged or cut off | Step 7 check, then download again |
| `Path does not exist: .../data/raw/2019-Nov.csv`, or `not found. Download it first` | The CSV is missing, or sits in another folder | Step 7. The file must be exactly `data/raw/2019-Nov.csv` inside the repo |
| `KATA MISMATCH` with `Driver heap: 1.0 GiB`, a time zone other than `UTC`, or events from `07:00:00` | `conf/spark-defaults.conf` was not read | Check that `conf/spark-defaults.conf` exists in your clone (`git pull`) and that you run the repo's script, not a copy elsewhere |
| `KATA MISMATCH` with heap and time zone right, and `wc -c` right (step 7) | Should not happen: Spark picked a different 100,000 rows on your machine | Post the full output in the group; don't try to fix it yourself |
| `Service 'SparkUI' could not bind on port 4040. Attempting port 4041` | Another Spark session is still open | Harmless. Close the other one when you can |
| `Unable to load native-hadoop library for your platform` | Spark looks for optional native libraries | Harmless, ignore |

### Windows and WSL

| You see | Cause | Fix |
|---|---|---|
| `HADOOP_HOME and hadoop.home.dir are unset`, or `winutils.exe` | You are running Spark on Windows itself, not in WSL | Use WSL2 (step 1). Nothing else is supported |
| Everything that reads the CSV is very slow | The repo is under `/mnt/c/...` | Clone into `~` inside WSL (step 1) and keep the data there |
| `OutOfMemoryError`, or WSL closes itself / `wsl` restarts in the middle of a job | By default WSL gets only half of the laptop's RAM, and Spark takes 6 GB of it | In Windows, create `%UserProfile%\.wslconfig` with `[wsl2]` on one line and `memory=12GB` on the next, run `wsl --shutdown` in PowerShell, reopen Ubuntu. **Don't lower the 6g in `conf/`**. If your laptop cannot spare it, raise a red flag in the group |
| `Your hostname ... resolves to a loopback address` | A WSL networking quirk | Harmless warning |
| `Service 'sparkDriver' could not bind on a random free port` | WSL networking or a VPN | `export SPARK_LOCAL_IP=127.0.0.1` (add it to `~/.bashrc` if it keeps happening) |
| `apt update` fails with `Release file ... is not valid yet` | WSL's clock drifted while the laptop slept | `sudo hwclock -s`, or `wsl --shutdown` in PowerShell and reopen |
| `$'\r': command not found`, or odd errors in files you did not change | The repo was cloned with Windows git, so lines end in `\r\n` | Delete that clone and clone again inside WSL (step 1) |
| `sudo: unable to resolve host` right after installing | The new distro's hostname is missing from `/etc/hosts` | Harmless for this project. `wsl --shutdown` and reopen usually clears it |

## 10. Editor: VSCode extensions

Optional and personal. The editor is not part of the stack, so hard rule 1 (do not add
technologies) does not apply here — nothing in the pipeline depends on any of this. It is
listed because four people who have never written Spark get real autocompletion for
`pyspark.sql.functions`, and because you cannot read a Parquet file with `cat`.

**In WSL:** run this in a terminal **inside** the WSL window — the title bar says
`[WSL: Ubuntu-26.04]`, and the command confirms `Installing extensions on WSL`.
Extensions installed on the Windows side cannot see the repo or the venv.

```bash
code --install-extension ms-python.python \
     --install-extension ms-python.vscode-pylance \
     --install-extension ms-python.debugpy \
     --install-extension dvirtz.parquet-viewer \
     --install-extension mechatroner.rainbow-csv \
     --install-extension ms-azuretools.vscode-docker \
     --install-extension ms-ossdata.vscode-pgsql \
     --install-extension humao.rest-client
```

| Extension | What it gives you | Useful from |
|---|---|---|
| `ms-python.python` + `ms-python.vscode-pylance` | Interpreter selection, go-to-definition, autocompletion. `pyspark==4.1.3` ships `py.typed`, so `DataFrame` and `F.*` complete for real instead of falling back to `Any` | W38 |
| `ms-python.debugpy` | Breakpoints in Spark driver code | W38 |
| `dvirtz.parquet-viewer` | Opens `data/silver/event_date=*/part-*.parquet` as a table, for eyeballing the UTC+7 date shift and the seven `clean()` rules. Spot checks only — counts go through DuckDB | W39 |
| `mechatroner.rainbow-csv` | Colours the columns of `seed/holidays_2019.csv` and small extracts. **Never** open `data/raw/2019-Nov.csv` with it: 9 GB freezes the editor | W39 |
| `ms-azuretools.vscode-docker` | Cassandra and Postgres container logs and a shell inside them, without memorising compose flags. Pulls in `ms-azuretools.vscode-containers` as its dependency | W40 |
| `ms-ossdata.vscode-pgsql` | Runs `warehouse/ddl.sql` against the Postgres container from the open file | W41 |
| `humao.rest-client` | A committed `.http` file next to the FastAPI routers, so a teammate can replay an endpoint alone instead of asking for the curl you ran | W42 |

When `web/` exists in W42, add `dbaeumer.vscode-eslint` and `esbenp.prettier-vscode`; the
Vite scaffold brings the config they read.

**Then pick the interpreter**, or none of the Python ones help:

```
Ctrl+Shift+P  ->  Python: Select Interpreter  ->  ./.venv/bin/python
```

**Check:** open `processing/kata.py`. The bottom status bar names `.venv`, the
`from pyspark.sql import SparkSession` line has no warning underline, and typing `F.`
inside a function offers `col`, `when`, `window`.

### Two settings worth more than any extension

`.gitignore` ignores `.vscode/`, so this file never leaves your machine — each of us
creates it:

```jsonc
// .vscode/settings.json
{
  "files.watcherExclude": { "**/data/**": true },
  "search.exclude":       { "**/data/**": true }
}
```

From W40 the replayer writes a new JSON file into `data/stream_landing/` every few
seconds and Spark rewrites `data/checkpoints/` on every micro-batch. Without the
exclude, the editor's file watcher re-scans all of it continuously — during the demo.

### Debugging Spark

Breakpoints work in driver-side code, **including inside `foreachBatch`**, which runs on
the driver. They do **not** fire inside a UDF or anything else that runs on an executor:
those are separate Python worker processes the debugger never attached to. Debug that
code with `df.show()` and counts instead.

### Do not install

| | Why |
|---|---|
| Jupyter, Data Wrangler | The conventions ban notebooks for production code: hard to review, hard to rerun. The Python extension will keep offering them anyway |
| Any "Spark", "Databricks" or "Big Data" extension | They drive remote clusters. Everything here runs `local[*]` |
| A Cassandra extension | The maintained ones do not exist. Use `cqlsh` inside the container (W40) |
