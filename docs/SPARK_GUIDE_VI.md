# Hướng dẫn Spark cho Nhóm 15: cài đặt, chạy thử và hiểu từng file

Viết cho cả nhóm (Khang, Nguyên, Tín, Đắt). Không ai trong nhóm từng dùng Spark hay
Java, nên file này giải thích từ đầu. Nó thay cho buổi dạy chung và clip quay màn hình.

Bản tiếng Anh ngắn hơn là [SETUP_SPARK.md](SETUP_SPARK.md). Hai file mô tả **cùng một
quy trình**: ai sửa một lệnh ở file này thì sửa luôn ở file kia.

**Làm xong bạn sẽ có:** Java 21, môi trường Python riêng có PySpark 4.1.3, file dữ liệu
9 GB, và `python processing/kata.py` in ra `KATA OK`.

**Thời gian:** khoảng 30 phút cài đặt, cộng thời gian tải 9 GB dữ liệu.

**Ổ đĩa:** cần trống khoảng 14 GB (thêm 1,2 GB cho hai image Docker ở phần 4).

**Kẹt quá 48 giờ:** cắm cờ đỏ trong nhóm ngay, đừng đợi checkpoint thứ Tư.

| Phần | Nội dung | Khi nào đọc |
|---|---|---|
| [1](#phần-1--spark-là-gì) | Spark là gì, các khái niệm sẽ gặp | Trước khi cài |
| [2](#phần-2--cài-đặt-từng-bước) | Cài đặt từng bước, mỗi lệnh làm gì | W38 |
| [3](#phần-3--chạy-katapy-và-đọc-kết-quả) | Chạy `kata.py`, đọc từng dòng kết quả | W38 |
| [4](#phần-4--docker-cassandra-và-postgres) | Cài Docker, chạy hai container, kiểm tra kết nối | W38 |
| [5](#phần-5--w39-chạy-load_bronzepy-và-đọc-kết-quả) | Chạy `load_bronze.py` rồi `batch_silver.py` | Đầu W39 |
| [6](#phần-6--từng-file-nghĩa-là-gì) | Từng file trong repo làm gì, đọc từng đoạn code | Trước khi viết script đầu tiên |
| [7](#phần-7--những-gì-đã-thay-đổi-trong-w38-và-vì-sao) | Những gì đã thay đổi trong W38, và vì sao | Khi thắc mắc một con số |
| [8](#phần-8--khi-có-lỗi) | Bảng tra lỗi | Khi có lỗi |
| [9](#phần-9--tiện-ích-vscode) | Tiện ích VSCode nên cài, và hai dòng cấu hình | Sau khi cài xong, tuỳ bạn |
| [10](#phần-10--streaming-đọc-br1-từng-khối) | Streaming: đọc BR1 từng khối, đổi gì cho BR3, BR5, BR8 | Trước khi viết BR streaming ở W41 |

---

## Phần 1 — Spark là gì

Dữ liệu của mình là một file CSV 9 GB, 67,5 triệu dòng. Nếu đọc bằng pandas, cả file
phải nằm trong RAM, và laptop không đủ. Spark làm khác:

- chia file thành nhiều mảnh nhỏ (gọi là **partition**);
- xử lý các mảnh **song song** trên mọi lõi CPU;
- mỗi lúc chỉ giữ trong RAM phần đang cần.

Các khái niệm dưới đây sẽ gặp suốt đồ án:

| Khái niệm | Nghĩa | Gặp ở đâu |
|---|---|---|
| **JVM, Java** | Spark viết bằng Scala và chạy trên máy ảo Java (JVM). Dù mình chỉ viết Python, máy vẫn phải có Java | Bước 2 |
| **JDK, `JAVA_HOME`** | JDK là bộ Java cài bằng `apt`. `JAVA_HOME` là biến môi trường chỉ cho PySpark biết Java nằm ở đâu | Bước 2, 3 |
| **PySpark, py4j** | PySpark là thư viện Python để **điều khiển** Spark. Code Python không tự xử lý dữ liệu: nó gửi lệnh sang JVM qua cầu nối py4j, còn JVM làm phần việc nặng | `requirements.txt` |
| **`SparkSession`** | Cửa vào của Spark. Lần đầu tạo nó trong một chương trình Python là lúc JVM khởi động | `SparkSession.builder...getOrCreate()` |
| **`local[*]`** | Chạy Spark trong **một** JVM trên laptop, dùng hết lõi CPU (`*`). Không có cluster, không có Docker | `.master("local[*]")` |
| **Driver, executor** | Trên cluster thật, driver điều phối và các executor làm việc. Ở `local[*]`, hai vai này là **cùng một JVM** | Bẫy bộ nhớ, bước 6 |
| **Heap** | Vùng RAM JVM được phép dùng. Nó **cố định từ lúc JVM khởi động**, sau đó không đổi được | `spark.driver.memory 6g` |
| **DataFrame** | Một bảng dữ liệu kiểu Spark, giống bảng SQL | `spark.read.csv(...)` trả về DataFrame |
| **Schema** | Tên và kiểu dữ liệu của từng cột. CSV chỉ là chữ, không lưu kiểu, nên mình phải khai báo schema | `processing/schema.py` |
| **Lazy, action** | Các lệnh như `where`, `withColumn`, `groupBy` chỉ **ghi lại kế hoạch**, chưa đọc dòng nào. Chỉ khi gọi một *action* (`collect`, `count`, `first`, `write`) Spark mới chạy thật | Vì thế thanh tiến trình chỉ hiện ở cuối |
| **Partition, task, stage** | File 9 GB được chia thành mảnh 128 MB, tức 68 partition. Mỗi partition là một task, và một nhóm task chạy cùng đợt là một stage | `[Stage 0: ... (40 + 20) / 68]`: 40 task xong, 20 đang chạy, tổng 68 |
| **Parquet** | Định dạng file lưu dữ liệu theo cột, có nén, và mang sẵn schema. Đọc nhanh hơn CSV rất nhiều | `data/bronze/` |
| **Chia thư mục theo cột** | `partitionBy("event_date")` tạo một thư mục cho mỗi ngày. Truy vấn lọc theo ngày chỉ mở thư mục cần đọc (*partition pruning*) | `data/bronze/event_date=2019-11-01/` |

Một đoạn code Spark điển hình. Đọc từ trên xuống, để ý dòng nào thật sự chạy:

```python
spark = SparkSession.builder.master("local[*]").getOrCreate()      # JVM khởi động
df = spark.read.schema(EVENT_SCHEMA).csv("data/raw/2019-Nov.csv")  # chỉ là kế hoạch: đọc CSV
df = df.where("event_type = 'purchase'")                            # vẫn là kế hoạch: lọc
print(df.count())                                                   # ACTION: tới đây Spark mới đọc file
spark.stop()                                                        # tắt JVM
```

---

## Phần 2 — Cài đặt từng bước

Mỗi bước gồm ba phần: lệnh, lệnh đó làm gì, và dòng **Kiểm tra**. Kết quả chưa khớp
dòng Kiểm tra thì đừng qua bước sau.

### Bước 1. Ubuntu 26.04 (cài thẳng hoặc trong WSL2)

Mọi lệnh trong file này dành cho **Ubuntu 26.04**. Python 3.14 là bản Python duy nhất
Ubuntu 26.04 cung cấp, và cả bộ công cụ được ghim theo nó.

**Trên Windows: dùng WSL2, đừng chạy Spark thẳng trên Windows.** Spark trên Windows cần
thêm `winutils.exe` và biến `HADOOP_HOME`, rồi hỏng theo những cách không ai trong nhóm
gỡ được. WSL2 là một Ubuntu thật chạy bên trong Windows. Mở PowerShell:

```powershell
wsl --list --online              # tìm dòng Ubuntu 26.04 ở cột NAME
wsl --install -d <tên vừa tìm>   # rồi mở "Ubuntu" từ Start menu và tạo user
```

Trong Ubuntu, clone repo vào **thư mục nhà của Linux** (`~`), không clone vào `/mnt/c/`.
Ổ `C:` được nối vào WSL qua một cầu nối chậm, nên một file 9 GB nằm ở đó sẽ đọc chậm hơn
nhiều lần. Đắt phải thêm bạn làm collaborator trên GitHub trước.

```bash
cd ~
git clone https://github.com/Dat-TG/shop-insight.git
cd shop-insight
```

**Kiểm tra:**
- `grep VERSION_ID /etc/os-release` in ra `VERSION_ID="26.04"`;
- `pwd` in ra `/home/<tên bạn>/shop-insight`.

### Bước 2. Java 21 và module tạo môi trường ảo

```bash
sudo apt update
sudo apt install -y openjdk-21-jdk-headless python3.14-venv unzip
```

| Gói | Để làm gì |
|---|---|
| `openjdk-21-jdk-headless` | Java 21, bản không kèm giao diện đồ hoạ (Spark không cần). Spark 4.x cần Java 17 trở lên; nhóm ghim 21 để bốn máy giống hệt nhau |
| `python3.14-venv` | Ubuntu 26.04 có sẵn Python 3.14 nhưng **thiếu** module tạo môi trường ảo. Thiếu nó, bước 4 báo `ensurepip is not available`. Máy Đắt đã gặp lỗi này thật |
| `unzip` | Giải nén file tải từ Kaggle |

**Kiểm tra:** `java -version` in ra dòng đầu bắt đầu bằng `openjdk version "21.`

### Bước 3. Đặt JAVA_HOME

```bash
echo 'export JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"' >> ~/.bashrc
source ~/.bashrc
```

Dòng đầu trông rối. Đọc từ trong ra ngoài:

1. `command -v java` trả về `/usr/bin/java`. Đây chỉ là một lối tắt (symlink).
2. `readlink -f` lần theo lối tắt tới file thật:
   `/usr/lib/jvm/java-21-openjdk-amd64/bin/java`.
3. `dirname` lần thứ nhất bỏ `/java`, lần thứ hai bỏ `/bin`. Kết quả là thư mục gốc
   của Java: `/usr/lib/jvm/java-21-openjdk-amd64`.
4. `echo '...' >> ~/.bashrc` ghi dòng `export` vào cuối `~/.bashrc`, file chạy mỗi khi
   mở terminal. Nhờ đó terminal nào cũng có `JAVA_HOME`.
5. `source ~/.bashrc` áp dụng ngay cho terminal đang mở.

**Kiểm tra:**
- `echo $JAVA_HOME` in ra `/usr/lib/jvm/java-21-openjdk-amd64` (máy ARM thì đuôi là
  `-arm64`);
- `$JAVA_HOME/bin/java -version` lại in ra phiên bản 21.

Nếu máy từng cài Java cũ: chạy `sudo update-alternatives --config java`, chọn Java 21,
rồi mở terminal mới.

### Bước 4. Môi trường ảo (venv) và PySpark

```bash
cd ~/shop-insight
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

| Lệnh | Làm gì |
|---|---|
| `python3.14 -m venv .venv` | Tạo thư mục `.venv/`, chứa một bản Python **riêng** của dự án. Cài gì vào đó cũng không đụng tới Python của hệ thống. `.venv/` nằm trong `.gitignore`, nên mỗi người tự tạo |
| `source .venv/bin/activate` | "Bật" venv cho terminal hiện tại; dấu nhắc lệnh sẽ bắt đầu bằng `(.venv)`. **Mỗi terminal mới đều phải chạy lại lệnh này** |
| `pip install -r requirements.txt` | Cài đúng các phiên bản ghi trong `requirements.txt`. PyPI chỉ có PySpark 4.1.3 ở dạng mã nguồn nặng 434 MB, nên pip phải tự đóng gói. Máy Đắt mất 4 phút 18 giây; chờ là bình thường |

**Kiểm tra:** `python -c "import pyspark; print(pyspark.__version__)"` in ra `4.1.3`.

### Bước 5. Vì sao phải đúng `pyspark==4.1.3`

**Không bao giờ** chạy `pip install pyspark` mà không ghi phiên bản, và không chạy
`pip install -U`. Gõ `pip install pyspark` hôm nay sẽ cài bản 4.2.0, còn tutorial cũ trên
mạng thì bảo cài 3.5.

**PySpark 3.5.x làm sập cả tiến trình Python (segfault) trên Python 3.14.** Chuỗi nguyên
nhân như sau:

1. PySpark 3.5 mang theo một bản riêng của thư viện **cloudpickle 2.x**. Thư viện này
   biến hàm Python thành dãy byte để Spark gửi đi.
2. cloudpickle 2.x gọi `pickle._getattribute`, một hàm nội bộ của Python, và hàm đó đã
   đổi ở Python 3.14.
3. Mọi hàm Python mà Spark gửi sang tiến trình worker đều đi qua cloudpickle: UDF, lambda
   của RDD, và hàm `foreachBatch` khi chạy Spark Connect.

**Sửa ở W40:** bản cũ ghi "mọi hàm truyền vào `foreachBatch` đều đi qua cloudpickle". Câu
đó sai với chế độ `local[*]` cổ điển mà dự án dùng. Ở chế độ này `foreachBatch` **không**
bị pickle: `ForeachBatchFunction` (`pyspark/sql/utils.py`) là một callback py4j, chạy ngay
trong tiến trình Python của driver. Pin 4.1.3 vẫn giữ nguyên, chỉ lý do là "mọi hàm gửi
sang worker", không phải `foreachBatch`.

Nguy hiểm ở chỗ bản sai vẫn cài bình thường và chạy được nhiều script batch, rồi mới sập
ở UDF đầu tiên, khi đã quá muộn để tìm nguyên nhân. Bản 4.1.3 không bị lỗi này.

### Bước 6. Cấu hình Spark: `conf/spark-defaults.conf` và hai cái bẫy

Repo có sẵn file [`conf/spark-defaults.conf`](../conf/spark-defaults.conf) với hai dòng:

| Dòng | Để làm gì |
|---|---|
| `spark.driver.memory 6g` | Heap của JVM. Không có dòng này thì heap chỉ 1 GB và các job lớn hết bộ nhớ |
| `spark.sql.session.timeZone UTC` | Bắt Spark đọc và in thời gian theo UTC, bất kể đồng hồ máy đặt múi giờ nào. Máy Việt Nam chạy UTC+7; nếu thiếu dòng này, sự kiện sau 17:00 UTC ngày 30/11 bị tính sang **01/12**, và bronze có 31 thư mục ngày thay vì 30 |

**Spark chỉ đọc file này nếu biến `SPARK_CONF_DIR` trỏ tới `conf/` TRƯỚC khi JVM khởi
động.** Bạn không phải tự đặt biến đó. Mọi script trong repo đều mở đầu bằng ba dòng này,
đặt trước khi tạo SparkSession:

```python
REPO = Path(__file__).resolve().parents[1]         # thư mục gốc của repo
sys.path.insert(0, str(REPO))                      # để script import được processing.schema
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # phải đứng trước SparkSession đầu tiên
```

- Dòng 1: `__file__` là đường dẫn của chính script; `.parents[1]` là thư mục cha của thư
  mục chứa script, tức gốc repo. Vì vậy script chạy đúng dù bạn đứng ở thư mục nào.
- Dòng 2: thêm gốc repo vào danh sách chỗ Python tìm module. Nhờ vậy
  `from processing.schema import EVENT_SCHEMA` chạy được cả từ `ingestion/`.
- Dòng 3: đặt biến môi trường. Khi SparkSession khởi động JVM, JVM đọc biến này để tìm
  `spark-defaults.conf`.

**Viết script Spark mới thì chép nguyên ba dòng này lên đầu.**

**Bẫy 1: đặt bộ nhớ trong code chỉ có tác dụng tuỳ lúc.** Nhiều tutorial viết như sau:

```python
# ĐỪNG LÀM: lúc có tác dụng, lúc bị bỏ qua mà không báo gì
SparkSession.builder.config("spark.driver.memory", "6g").getOrCreate()
```

Heap cố định từ lúc JVM khởi động, và mỗi chương trình Python chỉ khởi động JVM **một
lần**. Vì vậy dòng trên chỉ có tác dụng nếu **chính nó** là thứ khởi động JVM. JVM đã chạy
rồi thì cấu hình này bị bỏ qua: trong `pyspark` shell, trong notebook từ cell thứ hai trở
đi, hoặc trong script đã tạo session trước đó. Kết quả đo trên PySpark 4.1.3:

| Tình huống | Heap thật | `getConf()` báo |
|---|---|---|
| Session đầu tiên trong `python script.py` | 6.0 GiB (có tác dụng) | `6g` |
| Gọi `getOrCreate()` khi đang có session | 1.0 GiB | không có giá trị, kèm `WARN ... only runtime SQL configurations will take effect` |
| Tạo session mới sau `spark.stop()`, cùng chương trình | **1.0 GiB** | **`6g`**: cấu hình nói 6g nhưng heap thật chỉ 1 GB |

Dòng cuối là nguy hiểm nhất: không lỗi, không cảnh báo, cấu hình nhìn đúng, rồi một
tiếng sau job chết vì `OutOfMemoryError`. Vì vậy **cấu hình bộ nhớ chỉ đặt trong
`conf/spark-defaults.conf`**. Cách đó đúng trong mọi tình huống ở bảng trên. Cũng vì vậy
`kata.py` in heap **thật** của JVM chứ không in giá trị cấu hình.

**Bẫy 2: `spark.executor.memory` vô tác dụng ở đây.** Ở `local[*]`, driver chính là
executor, nên cấu hình dành cho executor không áp vào đâu cả. Đừng đặt, đừng chỉnh. Chỉ
`spark.driver.memory` có tác dụng.

**Kiểm tra:** phần 3 in cả hai giá trị này, đọc thẳng từ JVM đang chạy.

### Bước 7. Tải dữ liệu

Bộ dữ liệu là REES46 "eCommerce behavior data from multi category store" trên Kaggle:
<https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store>.
Mình chỉ cần file `2019-Nov.csv`. `data/` không đi qua git, nên mỗi người tự tải.

**Cách 1, bằng trình duyệt (dễ nhất).** Đăng nhập Kaggle, tải `2019-Nov.csv`; nếu nhận
được file `.zip` thì giải nén. Sau đó chép vào WSL:

```bash
cp /mnt/c/Users/<user Windows của bạn>/Downloads/2019-Nov.csv ~/shop-insight/data/raw/
```

**Cách 2, bằng dòng lệnh.** Cần token API Kaggle đặt ở `~/.kaggle/kaggle.json` và công cụ
Kaggle CLI. Chạy `pip install kaggle` trong venv là được, nhưng **đừng** thêm nó vào
`requirements.txt`.

```bash
kaggle datasets download -d mkechinov/ecommerce-behavior-data-from-multi-category-store -f 2019-Nov.csv -p data/raw/
unzip -o data/raw/2019-Nov.csv.zip -d data/raw/ && rm data/raw/2019-Nov.csv.zip
```

**Kiểm tra:** `wc -c data/raw/2019-Nov.csv` in ra đúng `9006762395`. Số nhỏ hơn nghĩa là
tải bị đứt giữa chừng; tải lại.

---

## Phần 3 — Chạy `kata.py` và đọc kết quả

```bash
source .venv/bin/activate
python processing/kata.py
```

`kata.py` đọc 100.000 dòng đầu của file CSV bằng Spark, đếm theo loại sự kiện, rồi so
với con số đúng. Nó chỉ cần `data/raw/`, không cần Docker hay bronze. Máy 20 lõi chạy
khoảng 10 giây; laptop nhỏ có thể tới một phút.

Trước kết quả sẽ có vài dòng log của Spark. **Các dòng sau là bình thường, bỏ qua:**

- `WARNING: Using incubator modules: jdk.incubator.vector`
- `Using Spark's default log4j profile`
- `WARN Utils: Your hostname, ... resolves to a loopback address`
- `WARN NativeCodeLoader: Unable to load native-hadoop library`
- thanh tiến trình `[Stage 0: ... ]`

**Kết quả đúng** (số phiên bản Python/Java có thể lệch ở chữ số cuối, `3.14.x`,
`21.0.x`; mọi con số khác phải khớp tuyệt đối):

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

| Dòng | Nó chứng minh điều gì |
|---|---|
| `Python ... Spark ... Java ...` | Đúng bộ công cụ đã ghim |
| `Driver heap: 6.0 GiB` | Spark **đã đọc** `conf/spark-defaults.conf`. Nếu thấy 1.0 thì file không được đọc |
| `Time zone: UTC` | Dòng múi giờ trong `conf/` đã có tác dụng |
| `Events from: 00:00:00 to 03:52:45` | Spark đọc đúng định dạng thời gian của file, **và** thật sự dùng UTC khi xử lý dữ liệu. Máy UTC+7 thiếu `conf/` sẽ in `07:00:00 to 10:52:45` |
| 4 dòng đếm | Đúng 100.000 dòng đầu, đếm đúng. `remove_from_cart` bằng 0 là **đúng**: file tháng 11 không có loại sự kiện này |
| `KATA OK` | Mọi dòng trên đều khớp. Có một dòng lệch thì script in `KATA MISMATCH` và thoát với mã lỗi 1 |

Các con số mong đợi được đếm **không dùng Spark**, bằng lệnh Linux thường:
`head -100001 data/raw/2019-Nov.csv | tail -n +2 | cut -d, -f2 | sort | uniq -c`.

**Post toàn bộ phần kết quả vào nhóm.** Vậy là xong phần cài đặt W38 của bạn.

---

## Phần 4 — Docker: Cassandra và Postgres

Hai server chạy trong container. **Cassandra** giữ năm bảng gold mà dashboard đọc ở W40.
**Postgres** giữ **hiện thực vật lý thứ hai** của star schema — `warehouse/ddl.sql`, Tín
nạp ở W39 — và các cấu hình benchmark ở W41.

Chỗ này quan trọng hơn bản kế hoạch cũ tưởng: Postgres **không phải** chỉ là baseline để
đo cho vui. `SYSTEM_DESIGN.md` mục 5.3 nói rõ — cùng một mô hình logic được hiện thực hai
lần (Parquet và Postgres), và chính điều đó làm phép so sánh "DuckDB trên Parquet star" với
"Postgres trên Postgres star" trở nên công bằng.

**Spark KHÔNG chạy trong Docker** (luật cứng số 1 trong `CLAUDE.md`), và phần 1-3 cũng
không cần Docker. Bronze với silver cũng không cần container nào cả — bạn chạy được trọn
phần 5 trong lúc Docker đang tắt.

**Nếu bạn đã làm xong phần 1-3 từ tuần trước thì bắt đầu thẳng từ đây — nhưng `git pull`
trước đã.** Phần này cần ba file chưa hề tồn tại lúc bạn clone, và một `requirements.txt`
vừa có thêm hai thư viện:

```bash
cd ~/shop-insight
git pull
ls docker-compose.yml .env.example serving/check_infra.py    # phải liệt kê đủ cả ba
```

Không pull thì `docker compose up` trả lời `no configuration file provided: not found`,
một câu không gợi ý gì về nguyên nhân.

### Ba khái niệm Docker, đủ để dùng

| Khái niệm | Là gì |
|---|---|
| **image** | Bản đóng gói sẵn của một phần mềm, tải từ mạng về. `cassandra:4.1.12` là một image. Nó chỉ đọc, không đổi |
| **container** | Một lần chạy của image đó, như một tiến trình. Xoá container không mất image |
| **volume** | Chỗ container ghi dữ liệu ra, nằm ngoài container. Nhờ nó, xoá container xong dữ liệu vẫn còn. `docker compose down -v` mới xoá volume |
| **`docker-compose.yml`** | File mô tả hai container: image nào, cổng nào, bộ nhớ bao nhiêu. Cả bốn máy chạy đúng file này |

Vì sao Cassandra và Postgres nằm trong container còn Spark thì không: hai server kia cần
**bốn máy giống hệt nhau** (cùng phiên bản, cùng cấu hình), và Docker cho đúng điều đó bằng
một dòng `image:`. Spark thì chạy `local[*]` — một JVM ngay trên máy bạn, không có cluster,
thêm Docker vào chỉ tốn một tuần mà không đổi được gì (luật cứng số 1).

Các thẻ image được ghim tới **số vá** (`cassandra:4.1.12`, chứ không phải `cassandra:4.1`),
lý do ghi ở `SYSTEM_DESIGN.md` mục 11.1: thẻ `4.1` tự đổi dưới chân bạn, và một node khởi
động ở bản vá này rồi khởi động lại ở bản vá khác là một buổi gỡ lỗi mà nhóm không có thời
gian cho nó.

### Bước 1. Cài Docker — Windows với WSL2

Cài **Docker Desktop for Windows**, giữ nguyên WSL2 backend mà nó chọn sẵn.

**Bước ai cũng quên:** Settings → Resources → **WSL Integration** → bật `Ubuntu-26.04` →
Apply & Restart. Rồi mở một cửa sổ Ubuntu **mới**. Docker Desktop tự đặt `/usr/bin/docker`
vào trong distro từ phía Windows; không bật nút đó thì trong Ubuntu không hề có lệnh
`docker`.

**Đừng** cài thêm `sudo apt install docker.io` bên trong WSL. Hai bản Docker chồng lên nhau
sinh ra lỗi không đọc nổi và image tự nhiên biến mất — phần 8 có dòng đó.

**Kiểm tra:** `docker version` in ra **cả** khối `Client` **và** khối `Server`. Chỉ có
`Client`, hoặc `Cannot connect to the Docker daemon`, là do nút WSL Integration hoặc do
Docker Desktop chưa chạy: xem phần 8, bảng "Windows và WSL".

### Bước 2. Cài Docker — Ubuntu cài thẳng

Dùng kho apt của chính Docker (<https://docs.docker.com/engine/install/ubuntu/>). Nó cho
`docker-ce` kèm **plugin `docker compose`** mà mọi lệnh trong repo này đều dùng. Gói
`docker.io` của Ubuntu và bản snap đều cũ hơn, lại kèm `docker-compose` v1 đã khai tử.

```bash
sudo usermod -aG docker $USER
```

rồi **đăng xuất và đăng nhập lại**. Một group vừa được thêm vào **không tồn tại** trong
phiên đăng nhập đã mở từ trước — đó là dòng đầu tiên của bảng lỗi phần 8, và ai cũng dính
đúng một lần.

**Kiểm tra:** `docker run --rm hello-world` in ra `Hello from Docker!`

### Bước 3. Giấy phép, cho sinh viên

Docker **Engine** trên Linux là Apache-2.0, miễn phí trong mọi trường hợp. Docker
**Desktop** miễn phí theo điều khoản Personal cho cá nhân, **giáo dục** và doanh nghiệp
nhỏ; đồ án môn học nằm trong đó, không ai phải trả tiền. (Ngưỡng này từng đổi — muốn chắc
thì xem <https://www.docker.com/pricing/>.)

**Kiểm tra:** không có. Đoạn này viết ra để không ai kẹt ở câu hỏi giấy phép.

### Bước 4. Chạy hai container

```bash
cd ~/shop-insight
docker compose up -d --wait
```

`-d` cho chúng chạy nền. `--wait` mới là phần quan trọng: nó chỉ trả quyền điều khiển lại
khi **cả hai container đã healthy**, chứ không phải vừa mới start. Cassandra cần 30-60 giây
mới mở cổng 9042, và nếu chỉ `up -d` thì lệnh ngay sau đó sẽ lỗi mà không hiểu vì sao.

Bạn **không cần** tạo file `.env`. `docker-compose.yml` tự lấy đúng các giá trị trong
`.env.example`. Chỉ khi nào cần đổi cổng hoặc mật khẩu mới `cp .env.example .env`.

Lần đầu phải tải khoảng 1,2 GB image. Đo trên máy 20 nhân: **75 giây** từ đầu, **19 giây**
cho những lần sau khi đã có image và volume.

**Kiểm tra:** `docker compose ps` hiện cả hai dòng `Up ... (healthy)`.

### Bước 5. Hai thư viện Python

`requirements.txt` có thêm `cassandra-driver` và `psycopg2-binary`, kèm bốn gói mà
`cassandra-driver` kéo theo. Cả hai đều có sẵn wheel dựng trước cho Python 3.14 — không cần
trình biên dịch, không cần `libpq-dev`.

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**Kiểm tra:** `python -c "import cassandra, psycopg2; print(cassandra.__version__)"` in ra
`3.30.1`.

### Bước 6. Kiểm tra kết nối

```bash
python serving/check_infra.py
```

**Kiểm tra:** kết quả kết thúc bằng `INFRA OK`, và các con số phải khớp.

```
cassandra 127.0.0.1:9042
  release_version       4.1.12          (expect 4.1.12: the docker-compose.yml tag)
  data_center           datacenter1     (the name the W40 driver will need)
  keyspace shopinsight  absent          (created by serving/apply_schema.py; either state is fine here)
postgres 127.0.0.1:5432
  server_version        16.15           (expect 16.15: the docker-compose.yml tag)
  current_database      shopinsight     (connected as shopinsight)
  shared_buffers        512MB           (expect 512MB: docker-compose.yml)
  maintenance_work_mem  256MB           (expect 256MB: room for the W39 GIN build)
  gin jsonb_path_ops    present         (expect present: postgres:16 needs no extension)
took                       0.2 s
INFRA OK
```

| Dòng | Nó chứng minh điều gì |
|---|---|
| `release_version 4.1.12` | Bạn đang chạy đúng image mà `docker-compose.yml` ghim, không phải một bản cũ còn nằm trong cache từ thẻ trôi `cassandra:4.1` |
| `data_center datacenter1` | Tên vùng mà `DCAwareRoundRobinPolicy` sẽ cần ở W40 — có sẵn trên màn hình rồi |
| `keyspace shopinsight absent` | **Đúng, không phải lỗi.** Nguyên tạo keyspace bằng `serving/apply_schema.py`. Script này cố tình không cần keyspace, nên nó chạy được **trước** khi file đó tồn tại |
| `server_version 16.15` | Như trên, cho Postgres |
| `current_database shopinsight` | Bạn vào đúng database container đã tạo, đúng role. Lệch nghĩa là `.env` bị sửa **sau** khi volume đã khởi tạo |
| `shared_buffers 512MB` | Cấu hình bộ nhớ trong `docker-compose.yml` thật sự đã tới được server |
| `maintenance_work_mem 256MB` | Đây là chỗ GIN index của Tín ở W39 (trên cột `dim_product.attributes`) có để dựng |
| `gin jsonb_path_ops present` | `postgres:16` có sẵn lớp toán tử này trong lõi, nên `warehouse/ddl.sql` **không cần** `CREATE EXTENSION` |
| `took` | Dưới một giây. Script chỉ đọc, không tạo gì cả |

**Post toàn bộ khối này vào nhóm**, giống như đã post `KATA OK`. Xong bước này là xong phần
cài đặt W38 của bạn.

### Bước 7. Tắt, bật, và bài toán RAM

| Lệnh | Nó làm gì |
|---|---|
| `docker compose stop` | Dừng cả hai, giữ nguyên mọi thứ. `docker compose start` bật lại |
| `docker compose down` | Xoá luôn container. Dữ liệu vẫn còn trong volume |
| `docker compose down -v` | Xoá cả volume. Mất sạch dữ liệu hai kho — mà thứ gì trong đó cũng dựng lại được |

Máy 16 GB, WSL mặc định chỉ lấy một nửa (8 GB), và có ba thứ cùng muốn chỗ đó:

| Ai cần | Khoảng |
|---|---|
| Spark driver (`spark.driver.memory 6g`) | 6 GB heap, cả tiến trình khoảng 7 GB |
| Cassandra (`MAX_HEAP_SIZE=2G`) | khoảng 3 GB |
| Postgres (`shared_buffers=512MB`) | khoảng 1 GB |
| Tổng | **khoảng 11 GB trên 8 GB có** |

Hai cách sửa, theo thứ tự. Một là cho WSL thêm bộ nhớ: tạo `%UserProfile%\.wslconfig` với
`[wsl2]` ở dòng đầu và `memory=12GB` ở dòng sau, chạy `wsl --shutdown` trong PowerShell rồi
mở lại Ubuntu — đúng file mà bảng "Windows và WSL" ở phần 8 đã nhắc. Hai là cách luôn đúng:
**bronze và silver không cần container**, nên cứ `docker compose stop` trước khi chạy
`load_bronze.py` với `batch_silver.py`, xong thì `docker compose start`.

**Đừng bao giờ hạ `6g` trong `conf/`**, và đừng hạ heap Cassandra xuống dưới 1 GB — dưới
mức đó nó chập chờn theo kiểu trông y như lỗi trong code của bạn. Nếu máy bạn không kham nổi
ngay cả khi đã tắt container, cắm cờ đỏ trong nhóm.

**Kiểm tra:** `docker compose stop`, rồi `docker compose ps -a` hiện cả hai `exited` (lệnh
`docker compose ps` trần chỉ liệt kê container đang chạy nên sẽ ra bảng rỗng), và
`python processing/kata.py` vẫn in `KATA OK` trong lúc Docker đang tắt.

## Phần 5 — (W39) Chạy `load_bronze.py` và đọc kết quả

```bash
source .venv/bin/activate
python ingestion/load_bronze.py
```

Script này tạo tầng **bronze**: nó giữ khoảng 7% người dùng của file gốc, kèm **toàn bộ
lịch sử trong tháng** của họ, rồi ghi thành Parquet. Máy 20 lõi chạy 25 giây; laptop 4
lõi có thể mất vài phút.

**Kết quả đúng** (mọi máy phải ra **y hệt**):

```
rows               4,767,012
users                258,390
products             129,899
date directories          30   (expect 30: event_date=2019-11-01 .. event_date=2019-11-30)
null event_time            0   (expect 0)
took                      25 s
BRONZE OK
```

| Dòng | Ý nghĩa |
|---|---|
| `rows` | Số sự kiện trong bronze, trong mức mục tiêu W38 là 4,4 đến 5,0 triệu |
| `users`, `products` | Số người dùng và số sản phẩm khác nhau trong mẫu |
| `date directories 30` | Mỗi ngày một thư mục, đủ 1 đến 30/11. Thấy 31 là do múi giờ (xem bước 6) |
| `null event_time 0` | Không có dòng nào đọc hỏng thời gian |
| `BRONZE OK` | Cả năm dòng trên khớp **chính xác**. Script so từng số chứ không so theo khoảng, vì mẫu sai (ví dụ đọc `user_id` thành INT ra 4.713.498 dòng) cũng nằm trong khoảng 4,4 đến 5,0 triệu |

Kết quả nằm trên đĩa như sau:

```
data/bronze/
├── .gitkeep                     git theo dõi file rỗng này để thư mục tồn tại sau khi clone
├── _SUCCESS                     Spark tạo khi ghi xong trọn vẹn
├── event_date=2019-11-01/
│   ├── part-00000-....snappy.parquet
│   └── part-00001-....snappy.parquet
├── event_date=2019-11-02/
│   └── ...
└── event_date=2019-11-30/       tổng cộng 30 thư mục, 97 file Parquet, 112 MB
```

Tên thư mục `event_date=...` chính là giá trị cột `event_date`. Spark không lưu cột này
trong file; khi đọc lại, nó lấy giá trị từ tên thư mục.

**Post năm con số vào nhóm ở W39.** Bốn máy phải ra giống nhau; đây là bước đối chiếu
sớm, thay vì tới W44 mới phát hiện lệch.

### Ngay sau đó: chạy `batch_silver.py`

```bash
python processing/batch_silver.py
```

Script này đọc bronze, làm sạch theo **bảy quy tắc** (giải thích ở phần 6) rồi ghi tầng
**silver**. Máy 20 lõi chạy khoảng 15 giây.

**Kết quả đúng** (mọi máy phải ra **y hệt**):

```
rows                      4,754,015   (bronze 4,767,012, 12,997 dropped)
users                       258,330
products                    128,972
category_l1 'unknown'     1,534,249
category_l2 'unknown'     1,534,249
category_l3 'unknown'     3,428,388
brand 'unknown'             634,202
null values                       0   (expect 0; only category_code may be null)
price <= 0                        0   (expect 0)
event_date wrong                  0   (expect 0: the Vietnam date of event_time)
event_date range      2019-11-01 .. 2019-12-01   (expect 2019-11-01 .. 2019-12-01)
rows on 2019-12-01           25,859   (expect 25,859: 30 Nov 17:00-24:00 UTC)
event_time range      2019-11-01 07:00:02 .. 2019-12-01 06:59:49   (expect 2019-11-01 07:00:02 .. 2019-12-01 06:59:49)
directories           31 dates, 93 date/type   (expect 31 and 93)
took                             15 s
SILVER OK
```

| Dòng | Ý nghĩa |
|---|---|
| `rows` | Bronze trừ 12.996 dòng có giá ≤ 0 và 1 dòng thiếu `user_session` |
| `users`, `products` | Ít hơn bronze một chút: 60 người và 927 sản phẩm chỉ có dòng giá ≤ 0 |
| `category_l1 'unknown'` | Số dòng không có `category_code`, khoảng một phần ba. Đây là quy tắc 4: thiếu nó thì một phần ba lệnh insert của BR1 hỏng |
| `category_l3 'unknown'` | Nhiều hơn l1 vì phần lớn mã danh mục chỉ có hai cấp, ví dụ `electronics.smartphone` |
| `null values 0` | Không cột nào còn null, trừ cột `category_code` gốc (được giữ nguyên) |
| `event_date wrong 0` | Mọi dòng có `event_date` đúng bằng ngày của `event_time` **sau khi** đổi sang giờ Việt Nam |
| `2019-12-01` và `31 dates` | **Đúng, không phải lỗi.** File kết thúc lúc 23:59 ngày 30/11 theo UTC, tức 06:59 sáng 01/12 giờ Việt Nam. 25.859 sự kiện từ 17:00 đến 24:00 UTC ngày 30/11 thuộc về ngày 01/12. Ở bronze, 31 thư mục là lỗi múi giờ; ở silver, **30** thư mục mới là lỗi (quên đổi giờ) |
| `event_time range` | Bắt đầu lúc 07:00:02 ngày 01/11, tức 00:00:02 UTC: sự kiện đầu tiên của file |
| `93 date/type` | 31 ngày × 3 loại sự kiện, mỗi thư mục đúng một file |

Kết quả nằm trên đĩa như sau:

```
data/silver/
├── .gitkeep
├── _SUCCESS
├── event_date=2019-11-01/
│   ├── event_type=cart/part-....snappy.parquet
│   ├── event_type=purchase/part-....snappy.parquet
│   └── event_type=view/part-....snappy.parquet
├── ...
└── event_date=2019-12-01/       tổng cộng 31 thư mục ngày, 93 file Parquet, 136 MB
```

Thư mục chia hai tầng, ngày rồi loại sự kiện, để truy vấn chỉ mở đúng phần nó cần. Hỏi
"đơn mua ngày 29/11" thì Spark chỉ đọc `event_date=2019-11-29/event_type=purchase/` và bỏ
qua mọi thư mục khác mà không mở file nào. Kỹ thuật này gọi là *partition pruning*.

**Post các con số này vào nhóm ở W39, cùng lúc với số bronze.**

---

## Phần 6 — Từng file nghĩa là gì

### `requirements.txt`: danh sách thư viện Python

```
pyspark==4.1.3
py4j==0.10.9.9
cassandra-driver==3.30.1
psycopg2-binary==2.9.13
click==8.5.0
Deprecated==1.3.1
geomet==1.1.0
wrapt==2.4.1
```

- `==` nghĩa là **đúng phiên bản này**, không phải "từ bản này trở lên".
- `py4j` là cầu nối Python sang JVM mà PySpark cần. Nó cũng được ghim, để bốn máy giống
  nhau.
- `cassandra-driver` và `psycopg2-binary` vào từ **W38** cùng `serving/check_infra.py`
  (kế hoạch cũ ghi W40 — đã đổi). `cassandra-driver` còn là cách duy nhất project này ghi
  vào Cassandra ở W40: `foreachBatch` cộng driver Python thuần, không bao giờ dùng
  Spark-Cassandra connector (luật cứng số 2).
- `psycopg2-binary` chứ không phải `psycopg2`: bản nguồn cần `libpq-dev` và `gcc`, còn bản
  `-binary` có wheel dựng sẵn cho Python 3.14.
- `click`, `Deprecated`, `geomet`, `wrapt` là phụ thuộc của `cassandra-driver`, ghim y như
  `py4j`: bốn máy, một bộ phiên bản.
- Ai cần thêm thư viện thì ghi kèm `==phiên bản` vào file này, trong **cùng PR** với code
  đầu tiên dùng thư viện đó.

### `conf/spark-defaults.conf`: cấu hình Spark dùng chung

Xem bước 6. File chỉ có hai dòng cấu hình, phần còn lại là chú thích. Luật cứng số 3
(chưa có số đo thì chưa tối ưu) nghĩa là không thêm cấu hình "cho nhanh" trước khi có
benchmark ở W41.

### `processing/schema.py`: schema của sự kiện, khai báo đúng một chỗ

Nó định nghĩa `EVENT_SCHEMA`, gồm 9 cột theo đúng thứ tự trong file CSV:

| Cột | Kiểu Spark | Ví dụ | Ghi chú |
|---|---|---|---|
| `event_time` | `TimestampType` | 2019-11-01 00:00:00 UTC | thời điểm xảy ra sự kiện |
| `event_type` | `StringType` | view | file tháng 11 chỉ có view, cart, purchase |
| `product_id` | `LongType` (số nguyên 64 bit) | 1003461 | |
| `category_id` | `LongType` | 2053013555631882655 | quá lớn cho 32 bit |
| `category_code` | `StringType` | electronics.smartphone | trống trong CSV, Spark đọc thành **NULL** (32,4% số dòng) |
| `brand` | `StringType` | xiaomi | trống trong CSV, Spark đọc thành **NULL** (14,9%) |
| `price` | `DecimalType(10, 2)` | 489.07 | số thập phân chính xác, không dùng float cho tiền |
| `user_id` | `LongType` | 520088904 | **bắt buộc là 64 bit**, xem dưới |
| `user_session` | `StringType` | 4d3b30da-... | mã phiên |

- **Vì sao khai báo tay mà không để Spark tự đoán (`inferSchema`)?**
  1. Để tự đoán, Spark phải đọc thêm trọn 9 GB một lượt.
  2. Nó đoán `user_id` là INT (32 bit), vì id lớn nhất 579.969.851 vừa 32 bit. Hàm
     `hash()` cho kết quả **khác nhau** với INT và với BIGINT, nên mẫu 7% sẽ là một nhóm
     người dùng khác hẳn. Đã đo: chỉ 18.150 người trùng nhau.
- **Vì sao "đúng một chỗ"?** Streaming (W40) cũng phải dùng đúng schema này: Structured
  Streaming không tự đoán được schema. Khai báo hai nơi thì sớm muộn hai bản sẽ lệch
  nhau. Ai cần schema thì `from processing.schema import EVENT_SCHEMA`.
- **Hai luật cho job streaming W40**, ghi ngay đầu `schema.py` để người viết streaming đọc
  thấy trước khi viết dòng đầu tiên:
  1. Job streaming đọc bằng schema này nhưng **không bao giờ ghi vào `data/silver/`**. Silver
     chỉ có một writer là `batch_silver.py`. Lý do ở phần `batch_silver.py` bên dưới.
  2. Job streaming phải dời `event_time` sang UTC+7 **và tính lại `event_date`** y hệt batch,
     bằng cách import `clean()` từ `batch_silver.py`, không chép lại luật. Quên bước này thì
     `gmv_by_minute` (BR1) xếp một sự kiện lúc 17:00-24:00 UTC vào ngày UTC, còn `funnel_daily`
     (BR2) xếp nó vào ngày hôm sau theo giờ Việt Nam: hai màn hình cãi nhau về ngày.
- `batch_warehouse.py` cũng import `EVENT_SCHEMA`, nhưng không để đọc (Parquet tự mang
  schema) mà làm thước đo: silver có cột nào lệch kiểu so với `EVENT_SCHEMA`, ví dụ `user_id`
  thành INT, thì script dừng trước khi ghi đè bất kỳ bảng nào.
- `RAW_TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ss z"` mô tả cách thời gian được viết trong
  CSV (`2019-11-01 00:00:00 UTC`). Chữ `z` đọc phần tên múi giờ `UTC`, nên giá trị luôn
  được hiểu là UTC, dù máy đặt múi giờ nào.

### `processing/kata.py`: bài kiểm tra cài đặt

Đọc từ trên xuống:

1. **Ba dòng mở đầu** (bước 6), rồi `import`.
2. **Hằng số:** `RAW_CSV` (đường dẫn file), `ROWS = 100_000`, và các giá trị mong đợi
   `EXPECTED`, `EXPECTED_FIRST`, `EXPECTED_LAST`.
3. **`check_environment(spark)`:**
   - hỏi JVM đang chạy qua py4j (`spark.sparkContext._jvm`) để lấy phiên bản Java và
     heap thật (`Runtime.getRuntime().maxMemory()`);
   - đọc múi giờ của session;
   - in ba dòng đầu, rồi trả về `True` nếu heap trên 5,5 GiB và múi giờ là UTC.
4. **`read_first_rows(spark)`** đọc CSV với bốn tuỳ chọn:
   - `header=True`: dòng đầu của file là tên cột, không phải dữ liệu;
   - `timestampFormat`: định dạng thời gian ở trên;
   - `mode="FAILFAST"`: gặp dòng không đọc được thì **dừng hẳn và báo lỗi**. Mặc định
     Spark lặng lẽ biến giá trị hỏng thành NULL;
   - `.schema(EVENT_SCHEMA)`, rồi `.limit(100_000)` để lấy 100.000 dòng.
5. **`main()`:**
   - kiểm tra file dữ liệu có tồn tại, tạo SparkSession, gọi `check_environment`;
   - `groupBy("event_type").agg(...)`: với mỗi loại sự kiện, đếm số dòng và lấy thời
     điểm sớm nhất và muộn nhất. `date_format` đổi thời điểm thành **chữ** ngay trong
     Spark (theo UTC). Nếu trả về kiểu thời gian, Python sẽ tự đổi sang giờ máy;
   - `.collect()` là **action**: lúc này Spark mới đọc file, và kết quả (vài dòng) được
     đưa về Python;
   - `spark.stop()` tắt JVM;
   - so từng con số với giá trị mong đợi, in `KATA OK` hoặc `KATA MISMATCH`
     (`sys.exit(1)`).

Hai chi tiết đáng nhớ khi tự viết query:

- **Spark chỉ đọc những cột query cần.** Nếu `kata.py` chỉ đếm theo `event_type`, Spark
  không đụng tới `event_time`, và `FAILFAST` không phát hiện được định dạng thời gian
  sai. Vì vậy kata cố ý lấy thêm thời điểm đầu và cuối.
- **Spark không hứa `limit()` lấy đúng những dòng đầu file.** Trên máy Đắt nó lấy đúng.
  Nếu máy bạn ra `KATA MISMATCH` trong khi heap, múi giờ và kích thước file đều đúng, hãy
  post kết quả vào nhóm (xem phần 8).

### `ingestion/load_bronze.py`: tạo tầng bronze

Đây là script **duy nhất** biến file CSV gốc thành dữ liệu cho dự án (`kata.py` chỉ đọc
thử 100.000 dòng). Từ W40, `replayer.py` đọc `data/bronze/`, không đọc file gốc.

Thứ tự trong `main()`:

1. **Kiểm tra file gốc** tồn tại và nặng đúng 9.006.762.395 byte. Việc này chạy
   **trước** mọi thứ khác, vì bước ghi sẽ xoá bronze cũ. File tải đứt thì script dừng
   ngay, không xoá gì.
2. **`read_raw(spark)`:** đọc toàn bộ CSV, cùng các tuỳ chọn như `kata.py` nhưng không
   có `limit`.
3. **`sample_users(events)`:** giữ những dòng thoả `pmod(hash(user_id), 100) < 7`.
   - `hash(user_id)` biến mỗi `user_id` thành một số nguyên bất kỳ, âm hoặc dương, theo
     thuật toán Murmur3 của Spark. Cùng một id thì **luôn** ra cùng một số, trên mọi máy.
   - `pmod(x, 100)` là phần dư **dương** khi chia cho 100, tức một số từ 0 đến 99.
   - `< 7` giữ những người rơi vào 7 "ô" trong 100 ô, khoảng 7% người dùng. Người được
     giữ thì giữ **mọi** sự kiện của họ, nên mỗi người có trọn lịch sử tháng 11.

   Ví dụ thật, tính bằng Spark trên máy Đắt:

   | `user_id` | `hash` (BIGINT) | `pmod(..., 100)` | Kết quả | Nếu đọc nhầm thành INT |
   |---|---|---|---|---|
   | 520088904 | 1181375224 | 24 | bỏ | `pmod` = 22, bỏ |
   | 530496790 | 1182385192 | 92 | bỏ | `pmod` = 59, bỏ |
   | 512927188 | -713643297 | **3** | **giữ** | `pmod` = 57, **bị bỏ nhầm** |

   Dòng cuối cho thấy vì sao kiểu của `user_id` quan trọng. Nó cũng cho thấy `pmod` xử
   lý số âm: -713643297 chia 100 dư -97, và `pmod` đổi thành 3.

   Lấy mẫu theo **người dùng**, không phải 5 triệu dòng **đầu** file. File xếp theo thời
   gian, nên 5 triệu dòng đầu chỉ là khoảng hai ngày đầu tháng. BR4 (RFM) sẽ mất ý
   nghĩa recency, và BR6 không đủ 7 ngày để tính `velocity_7d`. Không dùng số ngẫu
   nhiên hay `.sample()`: `data/` không đi qua git, nên bốn máy chỉ ra cùng một tập dữ
   liệu khi quy tắc chọn là **tất định**.
4. **`add_event_date(events)`:** thêm cột `event_date = to_date(event_time)`, tức ngày
   theo **UTC**, nhờ dòng múi giờ trong `conf/`. Bronze không làm sạch gì: nó là bản gốc
   để đối chiếu. Việc làm sạch và chuyển sang giờ Việt Nam (UTC+7) là của
   `batch_silver.py`.
5. **`write_bronze(events)`:** ghi Parquet.
   - `mode("overwrite")`: chạy lại thì **thay** bronze cũ, không ghi thêm bản thứ hai.
     Chạy lại bao nhiêu lần cũng ra cùng kết quả.
   - `partitionBy("event_date")`: mỗi ngày một thư mục.
   - `overwrite` xoá cả thư mục trước khi ghi, kể cả file `.gitkeep` mà git theo dõi.
     Khối `try/finally` tạo lại `.gitkeep` **kể cả khi ghi thất bại**. Nếu không,
     `git status` sẽ báo `.gitkeep` bị xoá, và ai đó có thể commit nhầm việc xoá.
   - Đây cũng là lúc Spark thật sự chạy: `write` là một action.
6. **`report(spark)`:** đọc lại bronze **từ đĩa**, không tin kết quả trong bộ nhớ. Nó
   đếm dòng, số người và số sản phẩm khác nhau, số dòng thiếu `event_time`, đếm thư mục
   ngày, rồi so từng số với `EXPECTED`.

### `processing/batch_silver.py`: tạo tầng silver

**Silver chỉ có đúng một writer là file này.** Job streaming ở W40 tuyệt đối không ghi vào
`data/silver/`, kể cả "chỉ ghi thêm sự kiện mới". Ghi từ hai nơi thì hỏng theo một trong
hai cách:

- Ghi bằng Parquet file sink: Spark tạo `data/silver/_spark_metadata/`, rồi từ đó chỉ đọc
  những file có tên trong đó. Mọi file `batch_silver.py` đã ghi trở nên vô hình với Spark,
  trong khi DuckDB vẫn thấy hết. Hai engine ra hai kết quả khác nhau trên cùng thư mục.
- Ghi bằng `foreachBatch`: nhân đôi dòng. Replayer phát lại bronze, mà bronze đã nằm sẵn
  trong silver. Từ lần demo thứ hai, BR2, BR4 và BR7 đếm mọi thứ gấp đôi.

Thứ tự trong `main()`:

1. **Kiểm tra bronze đã có chưa.** Chưa có thì dừng và nhắc chạy `load_bronze.py`, không
   xoá silver cũ.
2. **`read_bronze(spark)`:** đọc Parquet. Không cần truyền schema, vì file Parquet tự mang
   schema. Cột `event_date` của bronze (ngày theo **UTC**) quay lại từ tên thư mục;
   `clean()` sẽ thay nó.
3. **`clean(events)`:** bảy quy tắc.

   | # | Quy tắc | Vì sao |
   |---|---|---|
   | 1 | Bỏ dòng `price <= 0` | 12.996 dòng. Giá 0 hoặc âm không phải giao dịch thật |
   | 2 | Bỏ dòng `user_id` null | Bronze không có dòng nào, nhưng dữ liệu streaming có cùng dạng |
   | 3 | Tách `category_code` thành `category_l1/l2/l3` | `electronics.smartphone` → `electronics`, `smartphone` |
   | 4 | Chỗ nào null thì **điền `'unknown'`** cho `category_l1/l2/l3` | 32,4% dòng của file gốc (21.898.171 / 67.501.979) không có `category_code`. `category_l1` là nửa khoá phân mảnh của `gmv_by_minute`, và Cassandra từ chối khoá null: không điền thì cứ 3 lệnh insert của BR1 hỏng 1 và GMV thiếu một phần ba |
   | 5 | `brand` null thì điền `'unknown'` | |
   | 6 | Đổi `event_time` sang UTC+7 **và tính lại `event_date` từ giờ mới** | Giữ `event_date` cũ là gán sai ngày cho mọi sự kiện 17:00-24:00 UTC, làm lệch BR1, BR2, BR6 |
   | 7 | Bỏ dòng `user_session` null | 1 dòng. `fact_event` cần cột này NOT NULL, và nó là clustering key của `abandoned_carts` (BR5) |

   Ba chi tiết dễ sai:
   - **`F.get(parts, 2)`, không dùng `getItem(2)`.** Spark 4 bật chế độ ANSI: lấy phần tử
     thứ 3 của một mảng chỉ có 2 phần tử (mã hai cấp như `electronics.smartphone`) làm
     **cả job dừng** với lỗi `INVALID_ARRAY_INDEX`. `get()` trả về null, rồi `coalesce`
     điền `'unknown'`.
   - **Đổi giờ trước, lấy ngày sau.** Phiên Spark chạy theo UTC (nhờ `conf/`), nên
     `to_date` của giờ đã đổi chính là ngày Việt Nam. Ví dụ 20:00 UTC ngày 30/11 thành
     03:00 ngày 01/12, nên được xếp vào `event_date=2019-12-01`.
   - **`clean()` không đọc, không ghi gì**: nhận DataFrame, trả DataFrame. Job streaming ở
     W40 import nó (`from processing.batch_silver import clean`) thay vì chép lại bảy quy
     tắc, nên không thể quên đổi giờ. Import một hàm không biến job streaming thành writer
     của silver. `clean()` còn tự kiểm tra phiên Spark có chạy theo UTC không: script nào
     quên dòng `SPARK_CONF_DIR` sẽ chạy theo giờ máy (UTC+7): `to_date` cộng thêm 7 giờ nữa
     và xếp mọi sự kiện 10:00-17:00 UTC sang ngày hôm sau mà không báo lỗi gì. Vì vậy
     `clean()` dừng hẳn với một thông báo rõ ràng.

   Cột `category_code` gốc được giữ nguyên, kể cả khi null: `dim_product` cần nó, và đó là
   chỗ duy nhất còn giữ cấp thứ tư của mã `electronics.audio.music_tools.piano`.
4. **`write_silver(events)`:** ghi Parquet.
   - `repartition("event_date", "event_type")` gom mỗi cặp (ngày, loại) về một chỗ, nên mỗi
     thư mục có đúng một file: 93 file trên mọi máy. Không có dòng này, mỗi file bronze tự
     ghi một file nhỏ vào mọi thư mục nó chạm tới, ra khoảng 580 file, và số "partition đã
     đọc" mà mỗi màn hình hiển thị sẽ phụ thuộc vào cách bronze tình cờ bị chia.
   - `partitionBy("event_date", "event_type")`: thư mục ngày, trong đó là thư mục loại sự kiện.
   - `mode("overwrite")` và khối `try/finally` giữ `.gitkeep`, giống hệt bronze.
5. **`report(spark)`:** đọc lại silver **từ đĩa** rồi so từng số với `EXPECTED`, như bronze.

### `docker-compose.yml`: hai container

Đọc từ trên xuống:

1. **`name: shopinsight`** — tên project của compose, để volume trên máy nào cũng tên
   `shopinsight_cassandra_data`, kể cả người clone vào thư mục tên khác.
2. **`image: cassandra:4.1.12`, `image: postgres:16.15`** — ghim tới số vá, không phải
   `4.1` / `16`. Thẻ ngắn tự đổi dưới chân bạn.
3. **`MAX_HEAP_SIZE: 2G` và `HEAP_NEWSIZE: 256M`** — phải đặt **cả hai**. Không đặt gì thì
   `cassandra-env.sh` lấy một phần tư RAM máy (khoảng 3,7 GB trong WSL 16 GB) trong khi
   Spark đã xin 6 GB. Đo trên 4.1.12: image này chạy CMS chứ không phải G1, mà dưới CMS
   script sẽ `exit 1` nếu chỉ đặt một trong hai.
4. **`command: postgres -c shared_buffers=512MB -c maintenance_work_mem=256MB`** — cấu hình
   *của hồ sơ*, không phải tinh chỉnh (luật cứng số 3: benchmark ở W41). `maintenance_work_mem`
   là chỗ GIN index của Tín ở W39 dựng trong đó.
5. **`${CASSANDRA_PORT:-9042}`** — lấy từ `.env` nếu có, không thì dùng 9042. Nhờ vậy clone
   mới không cần `.env` vẫn chạy được.
6. **`127.0.0.1:` trước cổng** — chỉ máy bạn kết nối được. Hai kho này không có mật khẩu
   Cassandra, không nên để wifi trường với tới.
7. **`volumes: cassandra_data:`** — volume có tên, **không** mount vào `data/`. `data/` bị
   `.gitignore` chặn trừ `.gitkeep`, mà container ghi bằng uid 999 thì sẽ hiện lên trong
   `git status` và vướng quyền của WSL.
8. **`healthcheck`** — dùng `cqlsh` chứ không dùng `nodetool`: `nodetool` báo "UN" từ trước
   khi cổng 9042 mở, nên `--wait` sẽ trả về quá sớm. `cqlsh` đi đúng giao thức mà
   `cassandra-driver` dùng.
9. **Không có `restart:`** — cố tình. Hai container này không được tự bật lại sau khi khởi
   động máy rồi âm thầm giữ 3 GB trong lúc bạn chạy Spark.

### `.env.example`: giá trị dùng chung

Cổng, tên database, user, mật khẩu — `docker-compose.yml` và các script Python đọc chung.

- `.env` bị `.gitignore` chặn, còn `.env.example` thì **không** (`.gitignore` đã có dòng
  `!.env.example`). Nên giá trị mặc định đi theo git, còn thay đổi riêng của bạn thì không.
- Bạn **không bắt buộc** phải copy file này. Chỉ `cp .env.example .env` khi cần đổi cổng
  hoặc mật khẩu.
- Mỗi dòng một `KEY=value`. **Không** dấu nháy, **không** chú thích sau giá trị trên cùng
  dòng — cả compose lẫn `read_env()` đều sẽ nuốt luôn phần chú thích vào giá trị.
- Mật khẩu `local_dev_only` **không phải bí mật**: nó bảo vệ một container trên laptop của
  bạn, và không có gì trong hai kho đó là không dựng lại được.
- `CASSANDRA_KEYSPACE=shopinsight` đã khai báo nhưng keyspace **chưa tồn tại** — Nguyên tạo
  nó ở `serving/apply_schema.py`.

### `serving/check_infra.py`: kiểm tra hạ tầng

Nó là `kata.py` của phần Docker: chạy xong in `INFRA OK`. Thứ tự đọc:

1. **Docstring** — mục đích, cách chạy, kết quả mong đợi nguyên văn, và một câu quan trọng:
   script này **không tạo gì cả**, không keyspace, không bảng, không dòng nào.
2. **Hằng số** `EXPECTED_CASSANDRA_VERSION`, `EXPECTED_POSTGRES_VERSION`,
   `EXPECTED_SHARED_BUFFERS`, `EXPECTED_MAINTENANCE_WORK_MEM` — lấy từ `docker-compose.yml`,
   sửa thì sửa cùng nhau.
3. **`read_env()`** — tám dòng đọc `.env.example` rồi cho `.env` đè lên. Không dùng
   `python-dotenv`: thêm một thư viện cho tám dòng là đi ngược luật cứng số 1 và số 4. W39
   `apply_schema.py` và `load_star_postgres.py` **import** lại hàm này chứ không chép, đúng
   như `streaming_gold.py` import `clean()` từ `batch_silver.py`.
4. **`check_cassandra()`** — `SELECT ... FROM system.local`: tên bảng đủ đầy đủ nên **không
   cần keyspace**, không cần `USE`. Rồi hỏi `system_schema.keyspaces` xem keyspace đã có
   chưa, nhưng **in ra thôi, không tính vào đậu/rớt** — nếu tính thì tới W39 script sẽ rớt
   đúng lúc Nguyên làm đúng việc của mình.
5. **`check_postgres()`** — đọc ngược `shared_buffers` và `maintenance_work_mem` ra khỏi
   server đang chạy, nên cấu hình không tới nơi thì thấy ngay bằng một lệnh, chứ không phải
   tới cuối buổi dựng index W39 mới biết. Và hỏi `pg_opclass` xem `jsonb_path_ops` có trong
   bản build không — đó là lớp toán tử của GIN index W39; `CREATE INDEX` thật là việc của
   `warehouse/ddl.sql`, không phải của W38.
6. **`main()`** — chạy **cả hai** rồi mới kết luận: một kho chết không được che mất tình
   trạng của kho kia.

**Không có vòng lặp retry**, cố tình. `docker compose up -d --wait` đã đợi hộ rồi, nên lỗi
ở đây là lỗi thật chứ không phải "Cassandra còn đang khởi động".

### Mẫu cho script mới

Mọi script tầng sau (`batch_silver.py`, `batch_warehouse.py`, ...) nên giống
`load_bronze.py`:

- ba dòng mở đầu;
- các hằng số đường dẫn;
- vài hàm thường (không class, không factory: luật cứng số 4);
- `main()`, cuối cùng in ra số dòng.

Script ghi vào `data/` thì dùng `try/finally` để giữ `.gitkeep` như trên. Checklist đầy
đủ nằm ở `.claude/skills/spark-job/SKILL.md`.

---

## Phần 7 — Những gì đã thay đổi trong W38, và vì sao

Các PR W38 đã merge: #3 (cài đặt Spark), #4 (bronze), #5 (bản hướng dẫn tiếng Việt
này), #6 và #7 (tiện ích VSCode), rồi `batch_silver.py` (silver) và hạ tầng Docker
(`docker-compose.yml`, `.env.example`, `serving/check_infra.py`).

### File mới

| File | Vai trò |
|---|---|
| `docs/SETUP_SPARK.md` | Hướng dẫn cài đặt, bản tiếng Anh |
| `docs/SPARK_GUIDE_VI.md` | File này |
| `requirements.txt` | Ghim `pyspark==4.1.3`, `py4j==0.10.9.9` |
| `conf/spark-defaults.conf` | Heap 6g, múi giờ UTC |
| `processing/schema.py` | `EVENT_SCHEMA` và định dạng thời gian của file gốc |
| `processing/kata.py` | Bài kiểm tra cài đặt |
| `ingestion/load_bronze.py` | Tạo `data/bronze/` |
| `processing/batch_silver.py` | Tạo `data/silver/` (thêm sau, cùng W38) |
| `docker-compose.yml` | Cassandra 4.1.12 + Postgres 16.15, ghim tới số vá |
| `.env.example` | Cổng, tên database, user, mật khẩu — compose và Python dùng chung |
| `serving/check_infra.py` | Hai driver Python nói chuyện được với hai container; in `INFRA OK` |

### File đã sửa

| File | Sửa gì |
|---|---|
| `README.md` | Trạng thái dự án; lệnh cài đặt; đoạn nói `spark-defaults.conf` "không phải file của repo" (giờ đã là file của repo); số liệu mẫu; cây thư mục |
| `requirements.txt` | Thêm 6 ghim: `cassandra-driver`, `psycopg2-binary` và bốn phụ thuộc |
| `docs/SETUP_SPARK.md` | Thêm mục 9 (Docker), đánh số lại 9→10 và 10→11, thêm 16 dòng bảng lỗi |
| `SYSTEM_DESIGN.md` | Mục 3.1 (số liệu mẫu, `remove_from_cart`), 8, 10 (thêm `conf/`), 11 và 11.1 (cấu hình, múi giờ, bẫy bộ nhớ) |
| `CLAUDE.md` | Số dòng mẫu, trạng thái hiện tại |
| `PLAN.md` | Số người dùng trong bronze, cách mô tả bẫy bộ nhớ |
| `docs/AI_USAGE.md` | Thêm phiên 4: AI đã làm gì, kiểm tra thế nào, sai chỗ nào |
| `.claude/` | Skill `spark-job` (ba dòng mở đầu, luật `.gitkeep`), skill `streaming-job`, agent `spark-reviewer` và hook `check_python.py` (con số, cách mô tả bẫy bộ nhớ) |

### Những điều đo ra khác với tài liệu cũ

1. **Số liệu mẫu cũ sai.** Tài liệu cũ ghi 4.694.166 dòng, 258.088 người, 127.693 sản
   phẩm. Lúc đó chưa máy nào có Java, nên mẫu đó không thể được lấy bằng hàm `hash()` của
   Spark. Spark cho **4.767.012 / 258.390 / 129.899**. Một bản viết lại hàm `hash()` của
   Spark bằng Python thuần, chạy trên toàn file, ra đúng ba số này.
   - Các con số **suy ra từ mẫu cũ** chưa được tính lại: số dòng các bảng star, số
     phiên bản SCD2, 12.659 sản phẩm có lượt mua, kích thước range-join.
     `SYSTEM_DESIGN.md` mục 3.1 ghi rõ sẽ đo lại ở W39.
2. **`user_id` phải là BIGINT.** Đọc thành INT thì mẫu gần như là một nhóm người khác
   (xem bảng ví dụ ở phần 6).
3. **Máy chạy múi giờ UTC+7.** Không ghim UTC thì bronze có 31 thư mục ngày.
4. **File tháng 11 không có `remove_from_cart`.** Toàn file chỉ có view 63.556.110,
   cart 3.028.930 và purchase 916.939.
5. **Bẫy `spark.driver.memory` được mô tả lại cho đúng.** Tài liệu cũ nói đặt trong code
   "luôn bị bỏ qua". Đo thật thì có lúc có tác dụng (xem bảng ở bước 6). Luật giữ nguyên:
   chỉ đặt trong `conf/`.
6. **Ubuntu 26.04 thiếu `python3.14-venv`**, nên bước 2 cài thêm gói này.
7. **Spark 4.x cần Java 17 trở lên**, không bắt buộc đúng 21. Nhóm vẫn ghim 21.
8. **Silver có 31 thư mục ngày, không phải 30.** Đổi sang giờ Việt Nam thì bảy giờ cuối
   của 30/11 (UTC) thành ngày 01/12. Nhóm giữ 25.859 dòng này (ngày 01/12 chỉ có từ 00:00
   đến 06:59).
9. **Có quy tắc thứ bảy: bỏ dòng thiếu `user_session`.** Bronze có đúng 1 dòng như vậy.
10. **Số dòng thiếu `category_code` trong file gốc là 21.898.171**, đếm lại bằng `awk` trên
    toàn file (một con số khác, 21.898.175, từng được nhắc tới; lệch 4 dòng).
11. **File gốc có một khoảng 38 giờ không có đơn mua nào**: từ 18:09 UTC ngày 14/11 đến
    08:32 UTC ngày 16/11 (01:09 ngày 15/11 đến 15:32 ngày 16/11 giờ Việt Nam). Lượt xem và
    giỏ hàng vẫn bình thường. Đây là lỗi của nguồn dữ liệu, không phải của code. Theo giờ
    Việt Nam, ngày 15/11 chỉ có 170 đơn mua so với 35.812 lượt thêm giỏ, nên phễu BR2 ngày
    đó gần bằng 0, GMV của BR1 phẳng trong khoảng đó, và BR8 sẽ báo bất thường. Chi tiết ở
    `SYSTEM_DESIGN.md` mục 3.1.
12. **Postgres nặng ký hơn kế hoạch cũ.** Nó là **hiện thực vật lý thứ hai** của star
    schema (`SYSTEM_DESIGN.md` mục 5.3), không chỉ là baseline benchmark. W39 Tín nạp
    `warehouse/ddl.sql` và dựng GIN index `jsonb_path_ops` trên cột `attributes` của
    `dim_product`. `postgres:16` có sẵn `jsonb` và lớp toán tử đó trong lõi — **không cần
    extension**, chỉ cần đủ RAM, nên `maintenance_work_mem=256MB` nằm thẳng trong
    `docker-compose.yml`. `check_infra.py` đọc ngược con số đó ra để chứng minh nó đã tới
    nơi.
13. **Vào group `docker` rồi vẫn `permission denied`.** Đo trên máy Đắt: `getent group
    docker` có tên mình, nhưng `id` trong shell đang mở thì không — phiên đó mở ra từ
    trước lúc được thêm vào group. Phải mở phiên mới (`wsl --shutdown` rồi mở lại Ubuntu).
14. **Phải chặn heap của Cassandra, và phải đặt theo cặp.** Mặc định `cassandra-env.sh` lấy
    một phần tư RAM máy — khoảng 3,7 GB trong WSL 16 GB — trong khi Spark đã xin 6 GB. Đo
    trên `cassandra:4.1.12`: image này chọn **CMS** chứ không phải G1 (`-XX:+UseG1GC` bị
    comment trong `/etc/cassandra/jvm11-server.options`), và dưới CMS thì script `exit 1`
    với `please set or unset MAX_HEAP_SIZE and HEAP_NEWSIZE in pairs` nếu chỉ đặt một
    trong hai. Đặt cả hai thì JVM khởi động với `-Xms2G -Xmx2G -Xmn256M`, không cảnh báo.
15. **`--wait` không phải tuỳ chọn cho đẹp.** Đo trên máy 20 nhân: `docker compose up -d
    --wait` mất 75 giây lần đầu (Cassandra mở cổng 9042 ở giây thứ 61) và 19 giây những
    lần sau. Chỉ `up -d` thì lệnh kế tiếp gặp `Connection refused`.

---

## Phần 8 — Khi có lỗi

Spark in lỗi Java rất dài. Tìm dòng bắt đầu bằng `Caused by:` hoặc chứa `Exception`, rồi
tra theo cột đầu của bảng dưới.

### Mọi máy

| Bạn thấy | Nguyên nhân | Cách sửa |
|---|---|---|
| `JAVA_HOME is not set`, hoặc `Java gateway process exited before sending its port number` | Chưa cài Java, hoặc `JAVA_HOME` sai hay chưa được nạp | Làm lại bước 2 và 3. Mở terminal mới rồi `echo $JAVA_HOME` |
| `UnsupportedClassVersionError ... class file version 61.0` | Máy đang dùng Java cũ (8 hoặc 11) | `sudo update-alternatives --config java`, chọn 21, mở terminal mới |
| `The virtual environment was not created successfully because ensurepip is not available` | Thiếu `python3.14-venv` | `sudo apt install -y python3.14-venv`, rồi `rm -rf .venv` và làm lại bước 4 |
| `error: externally-managed-environment` | Chạy `pip` khi chưa bật venv | `source .venv/bin/activate`, rồi chạy lại pip |
| `No module named 'pyspark'` | Terminal này chưa bật venv | `source .venv/bin/activate` |
| `Segmentation fault`, hoặc `Fatal Python error` | Cài sai phiên bản PySpark | `pip install -r requirements.txt`, rồi làm lại phần Kiểm tra của bước 4 |
| `Python in worker has different version` | Spark gọi nhầm Python ngoài venv | Bật venv. Vẫn lỗi thì `export PYSPARK_PYTHON="$(which python)"` |
| `Malformed records are detected in record parsing. Parse Mode: FAILFAST` | File CSV hỏng hoặc bị cắt | Làm phần Kiểm tra của bước 7, rồi tải lại |
| `Path does not exist: .../data/raw/2019-Nov.csv`, hoặc `not found. Download it first` | Chưa có file, hoặc file nằm sai chỗ | Bước 7. File phải nằm đúng `data/raw/2019-Nov.csv` trong repo |
| `... is N bytes, not 9,006,762,395: a partial download` | Tải đứt giữa chừng; `load_bronze.py` từ chối chạy | Tải lại (bước 7) |
| `KATA MISMATCH` kèm `Driver heap: 1.0 GiB`, múi giờ khác `UTC`, hoặc thời gian bắt đầu `07:00:00` | Spark không đọc `conf/spark-defaults.conf` | Kiểm tra repo có file đó (`git pull`), và bạn đang chạy script **trong repo**, không phải bản chép ra chỗ khác |
| `KATA MISMATCH` trong khi heap, múi giờ và `wc -c` đều đúng | Không nên xảy ra: Spark lấy 100.000 dòng khác trên máy bạn | Post toàn bộ kết quả vào nhóm, đừng tự sửa |
| `BRONZE CHECK FAILED` với file gốc đúng kích thước | Có ai đó đã sửa quy tắc lấy mẫu, `processing/schema.py` hoặc `conf/` | `git status` và `git diff` để tìm chỗ bị sửa |
| `Service 'SparkUI' could not bind on port 4040. Attempting port 4041` | Một Spark khác vẫn đang chạy | Vô hại. Tắt cái kia khi tiện |
| `Unable to load native-hadoop library for your platform` | Spark tìm thư viện tuỳ chọn không có sẵn | Vô hại, bỏ qua |
| `permission denied while trying to connect to the Docker API at unix:///var/run/docker.sock` | Bạn đã ở trong group `docker`, nhưng phiên shell này mở ra từ trước lúc đó | `getent group docker` có tên bạn, còn `id` trong shell này thì không. Mở phiên hoàn toàn mới: trong WSL chạy `wsl --shutdown` ở PowerShell rồi mở lại Ubuntu. Máy Linux thật thì đăng xuất rồi đăng nhập lại |
| `Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?` | Docker Desktop chưa chạy (Windows), hoặc `dockerd` chưa chạy (Ubuntu cài thẳng) | Mở Docker Desktop, đợi con cá voi ngừng động đậy. Ubuntu: `sudo systemctl start docker` |
| `no configuration file provided: not found` | Bạn không đứng trong thư mục repo, hoặc chưa `git pull` từ lúc `docker-compose.yml` được đẩy lên | `cd ~/shop-insight && git pull`, rồi `ls docker-compose.yml`. Phần 4 mở đầu bằng đúng chuyện này |
| `docker-compose: command not found` | Tutorial cũ. `docker-compose` v1 đã khai tử, thay bằng lệnh con `docker compose` | Dùng `docker compose`, **có dấu cách**. Mọi lệnh trong repo này đều vậy |
| `port is already allocated`, hoặc `bind: address already in use` ở 5432 / 9042 | Có thứ khác đang giữ cổng đó — một Postgres cài bằng apt, hoặc một bản cũ của chính stack này | `sudo ss -lptn 'sport = :5432'` chỉ ra thủ phạm. Hoặc tắt nó, hoặc `cp .env.example .env` rồi đổi `POSTGRES_PORT`: compose và `check_infra.py` đọc chung đúng một giá trị đó |
| `INFRA CHECK FAILED` kèm `connect FAILED ... Connection refused`, ngay sau `docker compose up -d` | Cassandra cần 30-60 giây mới mở cổng 9042, mà `up -d` trả về ngay khi container vừa start | Chạy `docker compose up -d --wait`, nó chỉ trả về khi cả hai healthcheck đã đậu, rồi chạy lại lệnh kiểm tra |
| `docker compose ps` hiện container Cassandra `exited (137)`, hoặc nó restart liên tục | Kernel giết nó: không đủ RAM cho heap JVM | Xem bài toán RAM ở phần 4 bước 7. Cho WSL thêm bộ nhớ, hoặc `docker compose stop` trong lúc chạy Spark. Đừng hạ `spark.driver.memory` |
| `ModuleNotFoundError: No module named 'cassandra'` hoặc `'psycopg2'` | Chưa bật venv trong terminal này, hoặc bạn cài `requirements.txt` từ trước khi hai gói này được thêm vào | `source .venv/bin/activate`, rồi `pip install -r requirements.txt` |
| `INFRA CHECK FAILED` kèm `<-- expected 4.1.12` hoặc `<-- expected 16.15` | Máy còn cache một image cũ, từ trước khi thẻ được ghim | `docker compose pull`, rồi `docker compose up -d --wait`. **Đừng** "sửa" bằng cách đổi thẻ trong `docker-compose.yml` |
| `password authentication failed for user "shopinsight"`, hoặc `role "..." does not exist` | Bạn đổi `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` trong `.env` **sau** khi volume đã tạo. Image chỉ đọc mấy biến đó lúc khởi tạo volume rỗng | `docker compose down -v` (xoá database — chưa có gì trong đó là không dựng lại được), rồi `docker compose up -d --wait` |
| `docker compose config` hiện sai cổng hoặc sai user, hoặc `.env` như bị bỏ qua | `.env` được đọc từ thư mục bạn **đang đứng** khi gõ `docker compose`, không phải thư mục chứa file | `cd ~/shop-insight` trước đã. `check_infra.py` in ra host và cổng nó thật sự dùng, ngay hai dòng đầu |
| `please set or unset MAX_HEAP_SIZE and HEAP_NEWSIZE in pairs when using CMS GC` | Một trong hai biến bị xoá khỏi `docker-compose.yml`. `cassandra:4.1.12` chạy CMS, cần cả hai hoặc không cái nào | Đặt lại cả hai. Thiếu một cái là container `exit 1` |
| `manifest for cassandra:4.1.12 not found` (hoặc `postgres:16.15`) | Thẻ đã ghim không có trong registry | **Đừng** lùi về `cassandra:4.1`. Post vào nhóm: thẻ được đổi ở `docker-compose.yml` và `SYSTEM_DESIGN.md` 11.1 cùng một PR |

### Windows và WSL

| Bạn thấy | Nguyên nhân | Cách sửa |
|---|---|---|
| `HADOOP_HOME and hadoop.home.dir are unset`, hoặc `winutils.exe` | Đang chạy Spark thẳng trên Windows | Dùng WSL2 (bước 1). Nhóm không hỗ trợ cách nào khác |
| Mọi thao tác đọc CSV đều rất chậm | Repo nằm dưới `/mnt/c/...` | Clone lại vào `~` trong WSL (bước 1) và để dữ liệu ở đó |
| `OutOfMemoryError`, hoặc WSL tự tắt giữa chừng | Mặc định WSL chỉ được một nửa RAM của laptop, mà Spark lấy 6 GB | Trong Windows, tạo file `%UserProfile%\.wslconfig`: dòng đầu `[wsl2]`, dòng sau `memory=12GB`. Chạy `wsl --shutdown` trong PowerShell rồi mở lại Ubuntu. **Đừng giảm 6g trong `conf/`**; máy không đủ RAM thì cắm cờ đỏ trong nhóm |
| `Your hostname ... resolves to a loopback address` | Đặc điểm mạng của WSL | Chỉ là cảnh báo, bỏ qua |
| `Service 'sparkDriver' could not bind on a random free port` | Mạng WSL hoặc VPN | `export SPARK_LOCAL_IP=127.0.0.1` (thêm vào `~/.bashrc` nếu lỗi lặp lại) |
| `apt update` báo `Release file ... is not valid yet` | Đồng hồ WSL bị lệch sau khi laptop ngủ | `sudo hwclock -s`, hoặc `wsl --shutdown` rồi mở lại |
| `$'\r': command not found`, hoặc lỗi lạ ở file bạn không sửa | Repo được clone bằng git của Windows, nên dòng kết thúc bằng `\r\n` | Xoá bản clone đó, clone lại **bên trong** WSL (bước 1) |
| `sudo: unable to resolve host` ngay sau khi cài | Tên máy của distro mới chưa có trong `/etc/hosts` | Không ảnh hưởng dự án. `wsl --shutdown` rồi mở lại thường sẽ hết |
| `docker: command not found` trong Ubuntu, trong khi Docker Desktop đang chạy trên Windows | Chưa bật WSL integration cho distro này | Docker Desktop → Settings → Resources → **WSL Integration** → bật `Ubuntu-26.04` → Apply & Restart. Rồi mở cửa sổ Ubuntu **mới** |
| `docker version` in khối Client rồi tới `Server: ERROR` | Docker Desktop đang tắt, hoặc nút integration cho distro này bị tắt | Mở Docker Desktop, kiểm tra lại nút WSL Integration, mở terminal mới |
| Hai bản Docker: lỗi lạ, image tự nhiên biến mất | Bạn cài thêm `sudo apt install docker.io` trong WSL, chồng lên bản của Docker Desktop | `which docker` phải ra `/usr/bin/docker` — Docker Desktop tự đặt vào, dpkg không sở hữu nó (`dpkg -S /usr/bin/docker` không tìm thấy gì). Gỡ bản apt: `sudo apt remove docker.io docker-compose` |
| Client Windows (DBeaver, pgAdmin) không vào được 5432 / 9042 | Cổng cố tình chỉ mở trên `127.0.0.1`, để hai kho không mật khẩu không nằm trên mạng trường | Kết nối tới `localhost`, đừng dùng IP của WSL (`172.x.x.x`). Docker Desktop chuyển tiếp `127.0.0.1` sang localhost của Windows |
| WSL treo, hoặc job Spark chết, trong lúc hai container đang chạy | 6 GB driver của Spark cộng 2 GB heap Cassandra cộng Postgres không vừa nửa RAM mà WSL lấy mặc định | Bài toán RAM ở phần 4 bước 7: `%UserProfile%\.wslconfig` với `memory=12GB`, `wsl --shutdown`, mở lại. Và `docker compose stop` trước khi chạy `load_bronze.py` với `batch_silver.py` — cả hai đều không cần container |

---

## Phần 9 — Tiện ích VSCode

Không bắt buộc, và tuỳ mỗi người. Trình soạn thảo không nằm trong stack, nên luật cứng
số 1 (không thêm công nghệ) không áp dụng ở đây: không có bước nào trong pipeline phụ
thuộc vào mấy tiện ích này. Có mục này vì cả nhóm chưa ai viết Spark — cài Pylance thì
`pyspark.sql.functions` mới gợi ý đúng tên hàm — và vì file Parquet không đọc được
bằng `cat`.

**Nếu dùng WSL:** chạy lệnh dưới trong terminal **bên trong** cửa sổ WSL (thanh tiêu đề
ghi `[WSL: Ubuntu-26.04]`, và lệnh sẽ in `Installing extensions on WSL`). Tiện ích cài ở
phía Windows không nhìn thấy repo lẫn venv.

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

| Tiện ích | Được gì | Cần từ |
|---|---|---|
| `ms-python.python` + `ms-python.vscode-pylance` | Chọn trình thông dịch, nhảy tới định nghĩa hàm, gợi ý code. `pyspark==4.1.3` có sẵn file `py.typed`, nên `DataFrame` và `F.*` gợi ý thật chứ không rơi về `Any` | W38 |
| `ms-python.debugpy` | Đặt breakpoint trong code chạy ở driver | W38 |
| `dvirtz.parquet-viewer` | Mở `data/silver/event_date=*/part-*.parquet` dưới dạng bảng, để nhìn tận mắt việc dời giờ sang UTC+7 và bảy quy tắc trong `clean()`. Chỉ để xem nhanh — muốn đếm thì dùng DuckDB | W39 |
| `mechatroner.rainbow-csv` | Tô màu từng cột của `seed/holidays_2019.csv` và các file trích nhỏ. **Đừng bao giờ** mở `data/raw/2019-Nov.csv` bằng nó: 9 GB sẽ treo editor | W39 |
| `ms-azuretools.vscode-docker` | Xem log container Cassandra và Postgres, mở shell bên trong container mà không phải nhớ cờ của compose. Nó kéo theo `ms-azuretools.vscode-containers` | W38 |
| `ms-ossdata.vscode-pgsql` | Chạy thẳng `warehouse/ddl.sql` vào container Postgres từ file đang mở | W39 |
| `humao.rest-client` | Một file `.http` commit cạnh router FastAPI, để người khác gọi lại endpoint một mình thay vì phải hỏi bạn câu `curl` | W42 |

Tới W42 khi có thư mục `web/`, cài thêm `dbaeumer.vscode-eslint` và
`esbenp.prettier-vscode`; bản Vite dựng sẵn đã kèm file cấu hình cho hai cái đó.

**Sau đó phải chọn trình thông dịch**, không thì mấy tiện ích Python ở trên vô dụng:

```
Ctrl+Shift+P  ->  Python: Select Interpreter  ->  ./.venv/bin/python
```

**Kiểm tra:** mở `processing/kata.py`. Thanh dưới cùng hiện `.venv`, dòng
`from pyspark.sql import SparkSession` không bị gạch chân vàng, và gõ `F.` trong một hàm
thì hiện gợi ý `col`, `when`, `window`.

### Hai dòng cấu hình đáng giá hơn mọi tiện ích

`.gitignore` bỏ qua thư mục `.vscode/`, nên file này không đi theo git — mỗi người tự tạo
trên máy mình:

```jsonc
// .vscode/settings.json
{
  "files.watcherExclude": { "**/data/**": true },
  "search.exclude":       { "**/data/**": true }
}
```

Từ W40, replayer ghi một file JSON mới vào `data/stream_landing/` sau vài giây, còn Spark
ghi lại `data/checkpoints/` sau mỗi micro-batch. Không loại trừ hai thư mục đó thì bộ
theo dõi file của editor quét lại liên tục — đúng lúc đang demo.

### Gỡ lỗi Spark

Breakpoint có tác dụng với code chạy ở driver, **kể cả bên trong `foreachBatch`**, vì
`foreachBatch` chạy ở driver. Nhưng breakpoint **không** dừng bên trong UDF hay bất cứ
thứ gì chạy ở executor: đó là các tiến trình Python worker riêng, trình gỡ lỗi không hề
gắn vào. Chỗ đó cứ `df.show()` và đếm số dòng.

### Đừng cài

| | Vì sao |
|---|---|
| Jupyter, Data Wrangler | Quy ước của nhóm cấm dùng notebook cho code chạy thật: khó review, khó chạy lại. Tiện ích Python vẫn sẽ mời bạn cài chúng |
| Mọi tiện ích tên "Spark", "Databricks" hay "Big Data" | Chúng viết ra để điều khiển cluster từ xa. Cả dự án này chạy `local[*]` |
| Tiện ích Cassandra | Loại còn được bảo trì thì không có. Dùng `cqlsh` bên trong container (`docker compose exec cassandra cqlsh`) |

---

## Phần 10 — Streaming: đọc BR1 từng khối

BR1 là job streaming mẫu. Ở W41, BR3 (Khang), BR5 (Nguyên) và BR8 (Tín) chép đúng khung của
nó. Phần này đi qua `processing/streaming_gold.py` theo đúng đường một sự kiện đi, từng khối
một, và ở mỗi khối ghi rõ cái gì giữ nguyên, cái gì phải đổi cho BR của bạn. Mở file đó
song song khi đọc.

Bản tiếng Anh là [STREAMING_PATTERN.md](STREAMING_PATTERN.md). Hai bản mô tả **cùng một
khung**: sửa bản này thì sửa bản kia trong cùng PR.

```
replayer.py ──JSON mỗi 5 giây──> data/stream_landing/ ──> read_events ──> clean() ──> watermark
                                                                                          │
       Cassandra <── write_batch (foreachBatch) <── groupBy(window, ...) <────────────────┘
                             │
                   data/checkpoints/<job>/
```

### Đọc trước: hai cái bẫy của W41

**1. Spark không xếp hạng được trên streaming DataFrame, và ở chế độ update bạn cũng không
nhận đủ cả cửa sổ.** BR3 cần top 20 sản phẩm cho mỗi cửa sổ 15 phút. Trên luồng chỉ gộp được:
đếm view và cart theo `(window, product_id)`. Xếp hạng và cắt còn 20 phải làm trong
`write_batch`, nơi micro-batch là một DataFrame tĩnh bình thường, nên `Window`,
`row_number()`, `orderBy().limit()` đều dùng được. Nhưng như vậy vẫn chưa đủ. BR1 dùng
`outputMode("update")`, và chế độ này chỉ đưa cho `write_batch` **những dòng vừa thay đổi**
trong micro-batch. Xếp top 20 trên đó sẽ lặng lẽ bỏ sót mọi sản phẩm có số đếm không đổi.
BR3 phải dùng `outputMode("append")`: mỗi cửa sổ được đưa ra đúng một lần, đầy đủ, khi
watermark đã đóng nó lại.

**2. Mỗi bảng dọn dòng cũ theo một cách riêng.** Kiểu upsert thường của BR1 đúng với BR5 và
BR8, nhưng sai với BR3. Còn BR5 thì tuyệt đối không được thêm DELETE, dù trông gọn gàng đến
đâu.

| Bảng | Job | Khoá | `write_batch` làm gì | Vì sao |
|---|---|---|---|---|
| `gmv_by_minute` | BR1 | `((event_date, category_l1), window_start)` | upsert thường, không xoá | Khoá của một cửa sổ không bao giờ đổi, ghi lại thì đè đúng dòng cũ |
| `trending_products` | BR3 | `(window_start, rank)` | `DELETE FROM trending_products WHERE window_start = ?` rồi mới insert top 20 mới | Sản phẩm hạng 3 ở lần này, hạng 5 ở lần sau sẽ để lại hai dòng, và `LIMIT 20` trả nó hai lần. Partition chính là một cửa sổ, nên xoá cả partition trước là đúng |
| `abandoned_carts` | BR5 | `((event_date), user_session)` | upsert thường, **tuyệt đối không xoá** | Bảng tích luỹ suốt ngày. `DELETE ... WHERE event_date = ?` xoá sạch giỏ mà các micro-batch trước đã tìm ra, và màn hình tự rỗng giữa lúc demo. `cart_value` được cố ý để ngoài khoá, nên cùng một phiên luôn rơi đúng vào dòng của nó |
| `order_velocity_alerts` | BR8 | `((event_date), window_start, user_id)` | upsert thường, không xoá | Giống BR1: khoá của một (cửa sổ, user) không bao giờ đổi |
| `stockout_risk` | BR6, batch | `((warehouse_id), days_to_stockout, product_id)` | `DELETE ... WHERE warehouse_id = ?` rồi insert | Không phải streaming. Ghi vào đây cho đủ mọi luật ở một chỗ (SYSTEM_DESIGN 6.1) |

Hook `.claude/hooks/check_python.py` cảnh báo khi insert vào `trending_products` mà không có
DELETE đi kèm, hoặc khi có bất cứ lệnh DELETE hay TRUNCATE nào trên `abandoned_carts`. Lần đặt
lại duy nhất là `--fresh`, vốn chỉ gọi tên bảng qua `STREAMING_TABLES` nên không làm hook báo.

### Chạy

Hai terminal, **đúng thứ tự này**:

```bash
python processing/streaming_gold.py            # terminal 1. Đợi hai dòng READY
python ingestion/replayer.py --speed 60        # terminal 2, chỉ chạy sau READY
```

Điểm bắt đầu tốt cho demo: `--start "2019-11-17 08:00:00"`. Giờ UTC, tức 15:00 giờ Việt Nam,
trong ngày có nhiều lượt mua nhất của mẫu: 13.076, trong khi một ngày bình thường có khoảng
2.200. Như vậy mỗi file có khoảng 2.000 dòng. Mặc định bắt đầu lúc 00:00 UTC ngày 1/11, giờ
vắng nhất trong ngày: khoảng 90 dòng mỗi file. **Tránh ngày 15/11**: bronze có 432.575 sự
kiện hôm đó nhưng không có lượt mua nào, nên BR1 hiện GMV bằng 0 cả ngày.

Terminal 1 in ra (đo thật, ngày 17/11 từ 08:00 UTC):

```
READY: 1 of 4 jobs running (br1_gmv_by_minute), watching .../data/stream_landing
READY: now start python ingestion/replayer.py --speed 60
[br1_gmv_by_minute] batch 1: upserted 58 rows into gmv_by_minute (12 partitions) in 511 ms
[br1_gmv_by_minute] batch 1: 2,007 events after cleaning, watermark 2019-11-17 14:54:59, 1,150 ms
[br1_gmv_by_minute] batch 6: no window changed (watermark moved on)
```

Mỗi micro-batch in hai dòng. Dòng đầu do `write_batch` in: những gì đã ghi vào Cassandra.
Dòng sau lấy từ báo cáo tiến độ của Spark: bao nhiêu sự kiện còn lại sau các quy tắc lọc của
`clean()`, watermark đang ở đâu, và batch chạy mất bao lâu. Một batch "no window changed" chạy
vì watermark vừa dịch lên, và Spark bỏ trạng thái của những cửa sổ đã đóng. Số partition là
các ngành hàng có sự kiện trong 5 phút của batch, cộng thêm `all` (Khối 4).

| Tình huống | Lệnh |
|---|---|
| Chạy lần đầu, demo phát lại một khoảng thời gian đã phát, hoặc sau khi pull một thay đổi trong code của query | `python processing/streaming_gold.py --fresh` |
| Job bị dừng (Ctrl-C, sập) và cần chạy tiếp | `python processing/streaming_gold.py`, **không** có `--fresh` |

`--fresh` xoá `data/checkpoints/*/` và `data/stream_landing/*.json`, làm trống bốn bảng mà job
ghi (`gmv_by_minute`, `trending_products`, `abandoned_carts`, `order_velocity_alerts`), và
không đụng gì khác. Nó không bao giờ đụng tới `stockout_risk`, bảng do job batch của BR6 ghi.
Không có `--fresh` thì checkpoint còn nhớ watermark. Phát lại một khoảng thời gian cũ hơn sẽ bị
coi là "đến muộn" và bị bỏ mà không báo gì: màn hình chỉ đứng im.

Vì sao phải làm trống cả các bảng: màn hình hiện những dòng mới nhất của một partition. Phát
ngày 17/11 tới 20:54, rồi phát lại từ 15:00 mà không làm trống, thì các dòng mới nhất của mỗi
ngành hàng vẫn là 19:55–20:54 của lần cũ. Biểu đồ đứng im cho tới khi lần phát mới vượt qua
chúng. Đo ngày 30/9, khi `--fresh` chưa làm trống bảng: `electronics` dừng ở 20:54 trong khi
replayer mới tới 20:09. Mọi dòng trong các bảng này đều quay lại theo lần phát, và làm trống
một bảng trước khi query nào chạy là đặt lại từ đầu. Đó không phải kiểu xoá giữa chừng mà BR5
cấm.

Khởi động lại mà không có `--fresh` thì job chạy tiếp: file đã đọc không đọc lại, và cửa sổ
còn mở vẫn giữ nguyên tổng của nó. Đo trên Cassandra thật: sau khi khởi động lại, batch 8
nối tiếp đúng chỗ batch 7 dừng. Cả 3.772 dòng đang có trong `gmv_by_minute` (17/11, từ 15:00
tới 20:54 giờ Việt Nam) đều bằng đúng các phút tương ứng tính từ silver: GMV 1.794.180,25 và
5.618 đơn.

**Ctrl-C dừng giữa hai micro-batch.** Job in `Ctrl-C: stopping after the running micro-batch`,
để batch đang chạy ghi xong vào Cassandra (1–2 giây khi chỉ có BR1, tối đa 10), dừng lại, rồi in
`stopped; the checkpoints keep the progress`. Hai dòng
`WARN ... Failed to cancel job group ... Cannot find active jobs` là bình thường: không còn gì
đang chạy để huỷ. Bấm Ctrl-C lần nữa thì thoát ngay, và batch bị cắt ngang sẽ chạy lại khi
khởi động lại.

Việc này cần một dòng trong `main()`. Khởi động Spark sẽ thay trình xử lý Ctrl-C của Python
bằng trình của pyspark, vốn huỷ mọi job Spark đang chạy trước (`pyspark/core/context.py`).
Một batch bị bắt giữa chừng sẽ chết ngay trong lúc ghi và in ra một `StackOverflowError` của
Java. Đo ngày 30/9, gửi Ctrl-C lúc có batch đang chạy: trước khi sửa, 1 lỗi trong 7 lần thử
(4 trong 7 lần ghi ra lỗi khác); sau khi sửa, 0 trong 8, và batch nào đang chạy cũng commit
xong trước khi dừng.

### Khối 0: những dòng đầu file

```python
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts
os.environ["TZ"] = "UTC"
time.tzset()
```

Ba dòng đầu thì script Spark nào cũng có. Dòng `TZ` là dòng mới, và nó bảo vệ cả bốn job
trong file. PySpark đổi timestamp của Spark thành `datetime` của Python theo múi giờ **của
laptop**, chứ không theo session UTC của Spark (`TimestampType.fromInternal` gọi
`datetime.fromtimestamp`). Đo trên laptop UTC+7 khi thiếu dòng này: một timestamp mà Spark
hiện là `2019-11-17 15:00:00` ra khỏi `collect()` thành `22:00:00`. cassandra-driver lại lưu
giá trị không có múi giờ đó là 22:00 UTC. Kết quả lệch bảy tiếng, không có lỗi nào, và mỗi
máy lệch một kiểu.

**BR của bạn:** không phải đổi gì, vì bạn viết trong cùng file.

### Khối 1: đọc luồng (`processing/source.py`)

```python
spark.readStream.format("json").schema(EVENT_SCHEMA).option("mode", "FAILFAST").load(LANDING_DIR)
```

- `.schema(EVENT_SCHEMA)` là bắt buộc, vì Structured Streaming không tự đoán được schema.
  Schema chỉ khai báo ở một chỗ là `processing/schema.py`.
- Không có `timestampFormat`. Replayer để Spark tự viết JSON, nên `event_time` đến dưới dạng
  `"2019-11-01T00:00:02.000Z"` và bộ đọc mặc định đọc lại được đúng như vậy. Đo thật: cả
  4.767.012 dòng bronze đi qua bước JSON này, và `exceptAll` theo cả hai chiều đều ra 0.
- `FAILFAST` nghĩa là một dòng không đọc được sẽ dừng query. Chế độ mặc định sẽ biến dòng đó
  thành null, mà `clean()` thì không bỏ `event_time` null.
- Nếu đổi sang Kafka (một lựa chọn ở W44, sau cổng chặn) thì chỉ sửa hàm này.

**BR của bạn:** không phải đổi gì. `main()` dựng luồng một lần rồi truyền cho hàm
`start_brN(events, cassandra)` của bạn.

### Khối 2: làm sạch, kể cả dời sang UTC+7

```python
events = clean(read_events(spark)).withWatermark("event_time", WATERMARK)
```

`clean()` được **import** từ `processing/batch_silver.py`, không chép lại. Nhờ vậy luồng áp
dụng đúng bảy quy tắc của silver:

- `price > 0`
- phải có `user_id`
- tách `category_l1/l2/l3`, cấp nào thiếu thì điền `'unknown'`. `category_l1` là một nửa khoá
  partition của `gmv_by_minute`, mà Cassandra từ chối null trong khoá, nên thiếu bước điền
  này thì cứ ba lần insert của BR1 hỏng một.
- `brand` thiếu thì điền `'unknown'`
- **dời `event_time` sang UTC+7 và tính lại `event_date` từ giờ đã dời**
- phải có `user_session`, vì đó là khoá của BR5.

Quên dời giờ thì `gmv_by_minute` xếp một sự kiện lúc 17:00–24:00 UTC vào ngày UTC của nó,
trong khi `funnel_daily` (dựng bằng batch, từ silver) xếp nó vào ngày hôm sau, và hai màn hình
cãi nhau xem sự kiện thuộc ngày nào.

Import một hàm không biến job streaming thành người ghi silver. Xem bẫy A bên dưới.

**BR của bạn:** không phải đổi gì. `events` có đủ các cột của silver: `event_time` (giờ Việt
Nam), `event_type`, `product_id`, `category_id`, `category_code`, `category_l1/l2/l3`,
`brand`, `price`, `user_id`, `user_session`, `event_date`.

### Khối 3: watermark

```python
WATERMARK = "10 minutes"
```

Watermark cho Spark biết lúc nào một cửa sổ không còn thay đổi được nữa, để bỏ trạng thái của
nó đi. Không có watermark thì trạng thái của mọi cửa sổ từ đầu tới giờ nằm mãi trong bộ nhớ
cho tới khi JVM chết. Watermark đặt trên `event_time` **đã dời giờ**, nên nó cũng là giờ Việt
Nam: log in ra đúng giờ đồng hồ đó. Replayer gửi sự kiện theo đúng thứ tự thời gian, nên
không sự kiện nào trễ tới 10 phút. Watermark ở đây quan trọng vì bộ nhớ và vì chế độ append,
không phải vì dữ liệu đến muộn.

**BR của bạn:** không phải đổi gì, vì watermark dùng chung.

### Khối 4: gộp theo cửa sổ

```python
.groupBy(F.window("event_time", "1 minute"), "event_date", "category_l1")
.agg(
    F.sum(F.when(is_purchase, F.col("price")).otherwise(0)).alias("gmv"),
    F.count_if(is_purchase).alias("order_count"),
)
```

- BR1 cố ý giữ cả view và cart. Mẫu 7% chỉ có khoảng 1,5 lượt mua mỗi phút cho tất cả ngành
  hàng cộng lại, nên nếu lọc chỉ lấy lượt mua trước, phần lớn các phút sẽ biến mất khỏi biểu
  đồ. Giữ mọi sự kiện thì phút nào có hoạt động cũng có một dòng, với `gmv 0` nếu không bán
  được gì (API_CONTRACT §3 cho phép điều này).
- `event_date` nằm trong `groupBy` chỉ để mang khoá partition theo. Cửa sổ 1 phút không bao
  giờ vắt qua nửa đêm.
- Trước `groupBy`, mỗi sự kiện được nhân đôi: một lần dưới `category_l1` của nó, một lần dưới
  `'all'`:

  ```python
  .withColumn("category_l1", F.explode(F.array("category_l1", F.lit(ALL_CATEGORIES))))
  ```

  Nhờ vậy bộ lọc mặc định "Tất cả ngành hàng" chỉ đọc một partition thay vì 14. Dòng `all` ra
  từ chính phép gộp đó, nên không bao giờ thiếu. Cộng các dòng ngành hàng lại trong
  `write_batch` thì sai mà không báo lỗi gì: chế độ update chỉ đưa những ngành hàng thay đổi
  trong micro-batch này. Đo trên 150 phút đã đóng của ngày 17/11: `all` bằng đúng tổng 14 dòng
  ngành hàng, và bằng đúng silver, tới từng xu.

**BR của bạn:** **đừng** chép phép explode này. Nó chỉ dành cho BR1; ở BR5 hay BR8 nó sẽ
nhân đôi mọi con số, còn ở BR3 mỗi sản phẩm sẽ hiện hai lần.

| BR | Gộp theo | Tính gì |
|---|---|---|
| BR3 | `F.window("event_time", "15 minutes", "1 minute")`, `product_id` (thêm `brand`, `category_l1` cho đủ dòng) | `count_if` view, `count_if` cart |
| BR5 | theo `user_session`. `F.session_window("event_time", "30 minutes")` là một cách để nói "30 phút sau khi thêm giỏ mà không có gì" | có cart không, có mua không, giá trị giỏ, số món, thời điểm sự kiện cuối |
| BR8 | `F.window("event_time", "5 minutes")`, `user_id` | số lượt mua, tổng giá trị |

Kích thước cửa sổ lấy từ SYSTEM_DESIGN §8 bước 8.

### Khối 5: `foreachBatch` và ghi vào Cassandra

```python
insert = cassandra.prepare("INSERT INTO gmv_by_minute (...) VALUES (?, ?, ?, ?, ?)")

def write_batch(batch, batch_id):
    rows = batch.select(..., F.col("window.start").alias("window_start"), ...).collect()
    # one UNLOGGED BatchStatement per partition key
```

- `write_batch` chạy **ở driver**, mỗi micro-batch một lần. `batch` là một DataFrame tĩnh
  bình thường, nên mọi thứ bạn biết từ Spark batch đều dùng được ở đây, kể cả xếp hạng
  (bẫy 1).
- Ghi bằng `cassandra-driver` thuần Python. Spark-Cassandra connector bị cấm (luật cứng số 2
  trong CLAUDE.md).
- Chỉ có một prepared statement, Cassandra phân tích nó một lần. Các dòng được gom theo khoá
  partition thành từng batch UNLOGGED: mọi lệnh trong một batch cùng đi vào một partition, và
  đó là trường hợp duy nhất mà batch của Cassandra rẻ.
- `collect()` an toàn vì micro-batch nhỏ: khoảng 50–70 dòng với BR1. Với BR3, hãy cắt còn
  top 20 **trước** khi collect.
- **Timestamp:** Cassandra lưu giờ đồng hồ Việt Nam, cùng quy ước với silver. `cqlsh` hiện
  `2019-11-17 15:00:00+0000` cho 15:00 giờ Việt Nam, còn API thì gắn thêm `+07:00` khi trả
  giá trị ra. Khối 0 giữ cho điều này đúng.

**BR của bạn:** câu INSERT, luật xoá của bảng bạn (bẫy 2), và các cột bạn select.

### Khối 6: `writeStream`, checkpoint và trigger

```python
gmv_by_minute.writeStream
    .queryName("br1_gmv_by_minute")
    .outputMode("update")
    .foreachBatch(write_batch)
    .option("checkpointLocation", str(CHECKPOINT_DIR / "br1_gmv_by_minute"))
    .trigger(processingTime=TRIGGER)          # "5 seconds"
    .start()
```

- **Mỗi query một thư mục checkpoint riêng**, đặt tên `br<N>_<bảng>`. Hai query dùng chung
  một thư mục thì cả hai cùng hỏng.
- `update` hợp với BR1 và BR8: mỗi micro-batch phát lại những cửa sổ nó vừa đổi, kèm tổng
  tính tới lúc đó, nên màn hình thấy phút hiện tại lớn dần. BR3 cần `append` (bẫy 1). Với
  BR5, `append` hợp với câu hỏi: một phiên chỉ bị coi là bỏ giỏ khi đã qua 30 phút mà không
  mua, và chỉ watermark mới khẳng định được điều đó.
- Trigger kiểm tra file mới mỗi 5 giây. Đó cũng là nhịp của replayer, nên mỗi micro-batch
  xử lý khoảng một file.

**BR của bạn:** `queryName`, tên checkpoint, và `outputMode`.

### Khối 7: `main()`

`main()` kết nối Cassandra trước (thiếu container thì báo lỗi sau một giây, chứ không phải
sau mười giây chờ JVM khởi động). Nó dựng `events` một lần, gọi bốn hàm `start_brN`, và chạy
mọi query khác `None`. Sau đó nó đợi tới khi mỗi query đã đọc hết những gì có sẵn, in READY,
rồi mỗi micro-batch in một dòng tiến độ cho tới khi bạn bấm Ctrl-C. Khi bấm Ctrl-C,
`stop_between_batches()` để mỗi query chạy xong batch đang dở rồi mới dừng nó.

**BR của bạn:** thay thân hàm stub và trả về `StreamingQuery`. `main()` tự nhận nó, không phải
sửa chỗ nào khác.

### Những cái bẫy khó thấy trước

**A. Luồng không bao giờ ghi `data/silver/`.** Silver chỉ có một người ghi là
`batch_silver.py`. Ghi bằng file sink Parquet sẽ tạo `data/silver/_spark_metadata/`, và từ đó
Spark chỉ đọc những file có tên trong đó, nên mọi thứ batch đã ghi trở nên vô hình với Spark
(DuckDB vẫn thấy). Ghi qua `foreachBatch` thì nhân đôi dòng, vì replayer phát lại đúng bronze
mà silver đã chứa sẵn. BR2, BR4 và BR7 khi đó đếm mọi thứ hai lần. Đầu ra duy nhất là các
bảng Cassandra.

**B. Số shuffle partition bị ghim trong checkpoint.** Job này đặt
`spark.sql.shuffle.partitions` là 4, không phải 200 như mặc định của Spark. Đo thật với chỉ
BR1 trên máy 20 nhân: ở 200, mỗi micro-batch chạy 200 task state store và mất 3,5–6,7 giây
cho khoảng 50 sự kiện, lâu hơn cả trigger 5 giây. Ở 4, nó mất 1,0–1,7 giây cho khoảng 2.000
sự kiện. Mỗi query ghi giá trị này vào checkpoint ở lần chạy đầu tiên và bỏ qua mọi thay đổi
về sau, nên đổi giá trị xong thì phải chạy một lần với `--fresh`.

**C. Thứ tự khởi động là quan trọng.** File dồn trong `data/stream_landing/` trước khi một
query chạy lần đầu sẽ bị micro-batch đầu tiên của nó đọc hết một lượt, thành một batch khổng
lồ. Job in WARNING khi gặp tình huống này. Dừng lại, chạy với `--fresh`, rồi mới bật
replayer.

**D. Luật của replayer, cho ai sửa nó:**

- Nó đọc `data/bronze/` (258.390 user), không bao giờ đọc file CSV gốc (3.696.117 user). Tập
  người dùng lớn gấp 14 lần sẽ khiến ngưỡng correctness >= 99% không thể đạt được.
- Mỗi file được ghi dưới một tên ẩn (`.tmp-...`) rồi mới đổi tên. Spark bỏ qua file bắt đầu
  bằng dấu chấm, và đổi tên là thao tác nguyên tử, nên micro-batch không bao giờ đọc phải
  nửa file.
- Tên file là duy nhất cho mỗi lần chạy: `<lúc bắt đầu>-<số thứ tự>.json`. Checkpoint nhớ mọi
  đường dẫn đã đọc, và một tên bị lặp lại sẽ bị bỏ qua mà không báo gì.

**E. "events after cleaning" không phải "số dòng trong file".** Spark đẩy các điều kiện lọc
dòng của `clean()` xuống tận bước quét JSON, nên dòng tiến độ đếm những sự kiện còn lại sau
các điều kiện đó. Một file replayer 1.804 dòng hiện ra là 1.791. Đo trên sáu file, file nào
cũng khớp đúng.

**F. Pin toolchain, và lý do được nói lại cho đúng.** Xem phần 2, bước 5: pin 4.1.3 giữ
nguyên. Chỉ có câu "mọi hàm truyền vào `foreachBatch` đều đi qua cloudpickle" là sai với chế
độ `local[*]` dự án đang dùng.

### Danh sách cho Gate 1a (BR1, cuối W40)

- [ ] `docker compose up -d --wait`, `python serving/check_infra.py` in INFRA OK, và
      `python serving/apply_schema.py` in APPLY_SCHEMA OK.
- [ ] `python processing/streaming_gold.py --fresh` in READY, *rồi mới chạy*
      `python ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00"`.
- [ ] Ảnh 1: terminal 1 có ít nhất năm micro-batch, mỗi batch đủ hai dòng.
- [ ] Ảnh 2: `docker compose exec cassandra cqlsh -e "SELECT * FROM
      shopinsight.gmv_by_minute WHERE event_date = '2019-11-17' AND category_l1 = 'electronics'
      LIMIT 10"`. Dòng mới nhất nằm trên cùng (`window_start DESC`). Giờ trong bảng phải trùng
      với giờ "Vietnam" in trong log của replayer. Nếu lệch bảy tiếng thì Khối 0 bị thiếu.
      Chạy lại với `category_l1 = 'all'`: dòng tổng của từng phút.
- [ ] Ảnh 3: màn hình BR1 (`/br1`) khi API và replayer đang chạy. Đường biểu đồ dài thêm sau
      mỗi lần làm mới 10 giây; footer ghi `Cassandra · 1 partition`.
- [ ] Ctrl-C job: nó in `stopping after the running micro-batch`, rồi `stopped`, không có lỗi
      Java nào. Bật lại mà không có `--fresh`, và kiểm tra nó chạy tiếp mà không có batch
      khổng lồ nào.
- [ ] Ba ảnh để trong `docs/evidence/` và gửi lên nhóm chat.

### Mỗi BR đổi gì, gói trong một bảng

| | BR1 (xong) | BR3 | BR5 | BR8 |
|---|---|---|---|---|
| Hàm | `start_br1` | `start_br3` | `start_br5` | `start_br8` |
| Cửa sổ | 1 phút, nối tiếp nhau | 15 phút, trượt mỗi 1 phút | 30 phút sau khi thêm giỏ | 5 phút, nối tiếp nhau |
| Gộp theo | window, event_date, category_l1 | window, product_id | user_session | window, user_id |
| Output mode | update | **append** | append | update |
| Xếp hạng trong `write_batch` | không | **có**, top 20 | không | không |
| Xoá trước khi insert | không | **có**, `WHERE window_start = ?` | **không bao giờ** | không |
| Thêm dòng `all` (explode) | có | **không** | **không** | **không** |
| Checkpoint | `br1_gmv_by_minute` | `br3_trending_products` | `br5_abandoned_carts` | `br8_order_velocity_alerts` |
