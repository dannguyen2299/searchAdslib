# Facebook Ads Library Research Tool

Công cụ tìm kiếm và nghiên cứu quảng cáo Facebook/Instagram thông qua **Meta Ad
Library API** chính thức (endpoint `ads_archive` của Graph API).

## ⚠️ Đọc phần này trước khi dùng: API lấy được gì và không lấy được gì

Thông tin dưới đây được xác minh trực tiếp từ tài liệu chính thức của Meta
(`developers.facebook.com/docs/graph-api/reference/ads_archive/` và
`.../marketing-api/reference/archived-ad/`), không lấy từ blog bên thứ ba.

> **"Ads that did not reach any location in the EU will only return if they
> are about social issues, elections or politics."** — trích nguyên văn tài
> liệu chính thức của Meta, endpoint `ads_archive`.

Trên thực tế, với một quốc gia ngoài EU/UK (ví dụ **Việt Nam**):

- ✅ Quảng cáo chính trị / bầu cử / vấn đề xã hội chạy tại quốc gia đó — dữ liệu đầy đủ, phạm vi toàn cầu, lưu trữ tới 7 năm.
- ❌ Quảng cáo thương mại thông thường (ví dụ nhà xe, shop online) chỉ chạy trong quốc gia đó — **hoàn toàn không lấy được qua API này**, bất kể chọn `ad_type` hay `search_terms` nào. Những quảng cáo này vẫn có thể xem được nếu duyệt thủ công trên website `facebook.com/ads/library` (website công khai có phạm vi rộng hơn API), nhưng việc đó nằm ngoài phạm vi project này — tool chỉ dùng API chính thức, không scraping.

Với quốc gia thuộc EU/UK (`ad_reached_countries` là một nước EU hoặc `GB`),
`ad_type=ALL` trả về **mọi loại quảng cáo**, kể cả quảng cáo thương mại
thông thường.

Giao diện sẽ hiển thị cảnh báo này mỗi khi tìm kiếm với quốc gia ngoài
EU/UK, và response API cũng trả kèm trong `meta.limitation_notice`. Đây là
giới hạn cứng của API công khai từ Meta, không phải lỗi của tool.

## Kiến trúc

```
frontend/        HTML/CSS/JS tĩnh cho form tìm kiếm + hiển thị kết quả, chạy
                  qua nginx, proxy /api/* sang backend (không bao giờ gọi
                  Meta trực tiếp từ frontend)
backend/
  app/
    api/routes/ads.py        Controller: request -> validation -> service -> response
    services/                MetaAdLibraryService: orchestration, kiểm soát
                              pagination, cache, dedup, ranking, lưu DB
    clients/                 MetaAdLibraryClient: gọi HTTP thô tới ads_archive,
                              retry/backoff, phân loại lỗi theo type
    repositories/             AdRepository: upsert theo ad_id
    core/                     normalize.py, ranking.py, cache.py, errors.py, logging.py
    models/                   SQLAlchemy Ad model + Pydantic schemas
  tests/
    unit/                     logic thuần, không I/O
    integration/              MetaAdLibraryClient/service chạy với HTTP transport
                               ĐÃ MOCK
docker-compose.yml            backend + postgres + frontend
```

## Thiết lập Meta App

1. Tạo app tại [developers.facebook.com](https://developers.facebook.com/apps).
2. Xác minh danh tính tại [facebook.com/ID](https://www.facebook.com/ID)
   (upload giấy tờ tùy thân). Đây mới thực sự là bước quyết định quyền truy
   cập dữ liệu Ad Library — hướng dẫn của Meta cho Ad Library API trỏ tới
   bước này chứ không phải một permission OAuth thông thường. Thời gian xử
   lý thường vài ngày làm việc.
3. Tạo User Access Token (dùng Graph API Explorer để bắt đầu cũng được; nếu
   chạy service lâu dài, nên đổi sang long-lived token hoặc dùng System User
   token để không phụ thuộc vào việc một tài khoản cá nhân còn đăng nhập
   hay không).
4. **App Review**: không bắt buộc riêng cho Ad Library API — kết quả nhất
   quán ở mọi nguồn đã kiểm tra, vì đây là endpoint minh bạch công khai mà
   Meta muốn ai cũng truy cập được. App Review chỉ cần khi bạn thêm các
   scope Marketing API khác (`ads_management`,...) để quản lý ad account
   của business khác — không thuộc phạm vi project này.
5. **Business Verification**: không tìm thấy tài liệu chính thức nào yêu cầu
   Business Verification riêng cho `ads_archive` — thứ bắt buộc là xác minh
   danh tính *cá nhân* ở bước 2. Độ tin cậy của kết luận này ở mức trung
   bình (không có câu chữ xác nhận rõ ràng trong các trang đã fetch được) —
   nên kiểm tra lại trong Meta App Dashboard khi setup thật, vì chính sách
   của Meta có thể thay đổi.
6. Đặt token vào `.env` ở biến `META_ACCESS_TOKEN`. Tuyệt đối không commit
   token này.

## Biến môi trường

Copy `.env.example` thành `.env` và điền `META_ACCESS_TOKEN` (xem hướng dẫn
ở trên). Các biến còn lại đã có default hợp lý cho MVP — xem comment trong
`.env.example`.

## Chạy bằng Docker

```bash
cp .env.example .env
# sửa .env: điền META_ACCESS_TOKEN

docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000/api/ads/search
- Postgres: localhost:5432

Bảng dữ liệu được tạo tự động khi backend khởi động
(`Base.metadata.create_all`) — hiện chưa có công cụ migration, xem phần
Giới hạn hiện tại bên dưới.

## API

`GET /api/ads/search`

| Query param | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|
| `keyword` | có | — | truyền vào `search_terms` của Meta |
| `country` | không | `VN` | mã ISO 3166-1 alpha-2. Chỉ EU/UK mới có đầy đủ quảng cáo thương mại — xem cảnh báo ở trên |
| `status` | không | `ACTIVE` | `ACTIVE` \| `INACTIVE` \| `ALL` → tương ứng `ad_active_status` của Meta |
| `ad_type` | không | `ALL` | `ALL` \| `POLITICAL_AND_ISSUE_ADS` \| `HOUSING_ADS` \| `EMPLOYMENT_ADS` \| `FINANCIAL_PRODUCTS_AND_SERVICES_ADS` |

Response:

```json
{
  "data": [
    {
      "ad_id": "123456789",
      "page_id": "999",
      "page_name": "Nha Xe ABC",
      "body": "Xe Ha Noi Sai Gon chat luong cao...",
      "headline": "Xe Ha Noi Sai Gon",
      "description": "Dat ve ngay",
      "status": "ACTIVE",
      "start_date": "2026-08-12",
      "end_date": null,
      "platforms": ["facebook", "instagram"],
      "creative_url": null,
      "landing_url": null,
      "ad_library_url": "https://www.facebook.com/ads/library/?id=123456789"
    }
  ],
  "meta": {
    "total": 1,
    "keyword": "xe ha noi sai gon",
    "country": "VN",
    "status": "ACTIVE",
    "ad_type": "ALL",
    "limitation_notice": "'VN' is outside the EU/UK, so ..."
  }
}
```

Ghi chú về các field:
- `ad_library_url` ưu tiên dùng `ad_snapshot_url` do chính Meta trả về; nếu
  không có mới fallback sang URL tự dựng từ `ad_id` thật — không bao giờ
  dùng ID giả.
- `creative_url` và `landing_url` luôn là `null`: object `ArchivedAd` do
  `ads_archive` trả về không có field ảnh/video hay landing page URL.
  Frontend sẽ tự ẩn nút tương ứng khi các field này null thay vì đoán URL.
- `status` được suy ra từ việc `ad_delivery_stop_time` có rỗng hay không
  (theo đúng mô tả chính thức: rỗng nghĩa là quảng cáo vẫn đang chạy) — Meta
  không trả về field status tường minh.

Lỗi được trả về dạng `{"error": "..."}` kèm status code tương ứng — 401
(auth), 403 (permission), 429 (rate limit), 503 (Meta unavailable), 504
(timeout), 400 (bad request). Access token không bao giờ xuất hiện trong
error message hay log.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

- `tests/unit/` — logic thuần (normalize, tạo URL, keyword ranking, dedup,
  cache TTL). Không có network.
- `tests/integration/` — `MetaAdLibraryClient` và `MetaAdLibraryService`
  được test với HTTP transport **đã mock** (`respx`) hoặc fake client. Các
  test này chứng minh logic build request, pagination và phân loại lỗi của
  mình đúng; **không phải là bằng chứng API thật của Meta hoạt động y hệt
  trong production.**
- Repo này chưa có integration test gọi API thật (lúc build không có token
  thật). Trước khi đưa vào production, hãy chạy thử thủ công một lượt tìm
  kiếm với token thật đã xác minh danh tính, để chắc chắn response vẫn khớp
  với danh sách field trong `MetaAdLibraryClient.FIELDS`.

## Giới hạn hiện tại

- **Không lấy được quảng cáo thương mại ngoài EU/UK** — xem cảnh báo ở đầu
  tài liệu. Đây là giới hạn phạm vi lớn nhất, ảnh hưởng trực tiếp tới việc
  dùng tool để nghiên cứu quảng cáo thương mại tại Việt Nam.
- Chưa có công cụ migration (Alembic) — muốn đổi schema hiện phải
  `ALTER TABLE` thủ công hoặc tạo lại volume. Phù hợp cho MVP với 1 bảng;
  cần xem lại khi schema phức tạp hơn.
- Cache chạy in-process (`TTLCache`), không share giữa nhiều backend
  replica. Phù hợp MVP chạy 1 instance; nếu scale ra nhiều instance thì đổi
  sang Redis.
- Con số rate limit ~200 request/giờ trong comment code là số được nhiều
  nguồn cộng đồng report thống nhất, không tìm thấy bằng văn bản chính thức
  của Meta cho riêng endpoint này — logic retry/backoff dựa vào response
  thật `613`/`429` từ Meta làm nguồn chân lý, thay vì tự đếm trước theo con
  số đoán được.
- `creative_url`/`landing_url` luôn null — object `ArchivedAd` của Meta
  không expose các field này (xem phần API ở trên).
