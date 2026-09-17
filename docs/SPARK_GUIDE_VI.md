# Hướng dẫn Spark cho Nhóm 15: cài đặt, chạy thử và hiểu từng file

Viết cho cả nhóm (Khang, Nguyên, Tín, Đắt). Không ai trong nhóm từng dùng Spark hay
Java, nên file này giải thích từ đầu. Nó thay cho buổi dạy chung và clip quay màn hình.

Bản tiếng Anh ngắn hơn là [SETUP_SPARK.md](SETUP_SPARK.md). Hai file mô tả **cùng một
quy trình**: ai sửa một lệnh ở file này thì sửa luôn ở file kia.

**Làm xong bạn sẽ có:** Java 21, môi trường Python riêng có PySpark 4.1.3, file dữ liệu
9 GB, và `python processing/kata.py` in ra `KATA OK`.

**Thời gian:** khoảng 30 phút cài đặt, cộng thời gian tải 9 GB dữ liệu.

**Ổ đĩa:** cần trống khoảng 12 GB.

**Kẹt quá 48 giờ:** cắm cờ đỏ trong nhóm ngay, đừng đợi checkpoint thứ Tư.

| Phần | Nội dung | Khi nào đọc |
|---|---|---|
| [1](#phần-1--spark-là-gì) | Spark là gì, các khái niệm sẽ gặp | Trước khi cài |
| [2](#phần-2--cài-đặt-từng-bước) | Cài đặt từng bước, mỗi lệnh làm gì | W38 |
| [3](#phần-3--chạy-katapy-và-đọc-kết-quả) | Chạy `kata.py`, đọc từng dòng kết quả | W38 |
| [4](#phần-4--w39-chạy-load_bronzepy-và-đọc-kết-quả) | Chạy `load_bronze.py` | Đầu W39 |
| [5](#phần-5--từng-file-nghĩa-là-gì) | Từng file trong repo làm gì, đọc từng đoạn code | Trước khi viết script đầu tiên |
| [6](#phần-6--những-gì-đã-thay-đổi-trong-w38-và-vì-sao) | Những gì đã thay đổi trong W38, và vì sao | Khi thắc mắc một con số |
| [7](#phần-7--khi-có-lỗi) | Bảng tra lỗi | Khi có lỗi |

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
3. Mọi hàm truyền vào `foreachBatch` đều đi qua cloudpickle. Mà `foreachBatch` chính là
   cách dự án ghi vào Cassandra (luật cứng số 2 trong `CLAUDE.md`).

Nguy hiểm ở chỗ bản sai vẫn cài bình thường và chạy được mọi script batch. Nó chỉ sập ở
W40, lúc ghi streaming vào Cassandra, khi đã quá muộn để tìm nguyên nhân. Bản 4.1.3
không bị lỗi này.

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

## Phần 4 — (W39) Chạy `load_bronze.py` và đọc kết quả

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

---

## Phần 5 — Từng file nghĩa là gì

### `requirements.txt`: danh sách thư viện Python

```
pyspark==4.1.3
py4j==0.10.9.9
```

- `==` nghĩa là **đúng phiên bản này**, không phải "từ bản này trở lên".
- `py4j` là cầu nối Python sang JVM mà PySpark cần. Nó cũng được ghim, để bốn máy giống
  nhau.
- Ai cần thêm thư viện (ví dụ `cassandra-driver` ở W40) thì ghi kèm `==phiên bản` vào
  file này, trong **cùng PR** với code đầu tiên dùng thư viện đó.

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
  post kết quả vào nhóm (xem phần 7).

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

## Phần 6 — Những gì đã thay đổi trong W38, và vì sao

Hai PR đã merge: #3 (cài đặt Spark) và #4 (bronze).

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

### File đã sửa

| File | Sửa gì |
|---|---|
| `README.md` | Trạng thái dự án; lệnh cài đặt; đoạn nói `spark-defaults.conf` "không phải file của repo" (giờ đã là file của repo); số liệu mẫu; cây thư mục |
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
   (xem bảng ví dụ ở phần 5).
3. **Máy chạy múi giờ UTC+7.** Không ghim UTC thì bronze có 31 thư mục ngày.
4. **File tháng 11 không có `remove_from_cart`.** Toàn file chỉ có view 63.556.110,
   cart 3.028.930 và purchase 916.939.
5. **Bẫy `spark.driver.memory` được mô tả lại cho đúng.** Tài liệu cũ nói đặt trong code
   "luôn bị bỏ qua". Đo thật thì có lúc có tác dụng (xem bảng ở bước 6). Luật giữ nguyên:
   chỉ đặt trong `conf/`.
6. **Ubuntu 26.04 thiếu `python3.14-venv`**, nên bước 2 cài thêm gói này.
7. **Spark 4.x cần Java 17 trở lên**, không bắt buộc đúng 21. Nhóm vẫn ghim 21.

---

## Phần 7 — Khi có lỗi

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
