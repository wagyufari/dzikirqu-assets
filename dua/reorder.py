import json

INPUT_FILE = "hisn.json"
OUTPUT_FILE = "hisn_reordered.json"

ORDER = [
    # 1. Dzikir Umum & Tauhid
    "Pujian kepada Allah",
    "Memohon ampunan dan bertobat",
    "Keutamaan berselawat atas Nabi (ﷺ)",
    "Perlindungan dari Dajjal",
    "Karena takut syirik",

    # 2. Dzikir Harian
    "Dzikir Pagi",
    "Dzikir Petang",
    "Ketika bangun tidur",
    "Ketika membalikkan badan di malam hari",
    "Dzikir Sebelum tidur",
    "Ketika mengalami kegelisahan, ketakutan, kecemasan saat tidur",
    "Ketika melihat mimpi baik atau mimpi buruk",

    # 3. Pakaian & Kebersihan
    "Ketika mengenakan pakaian",
    "Ketika mengenakan pakaian baru",
    "Kepada orang yang mengenakan pakaian baru",
    "Ketika melepas pakaian",
    "Ketika masuk WC",
    "Ketika keluar WC",

    # 4. Wudhu
    "Sebelum wudhu",
    "Setelah Wudhu",

    # 5. Masjid & Shalat
    "Mengenai adzan",
    "Ketika pergi ke masjid",
    "Ketika masuk masjid",
    "Ketika keluar masjid",
    "Do'a setelah takbir (Iftitah)",
    "Ketika Ruku'",
    "Ketika bangkit dari posisi rukuk (I'tidal)",
    "Ketika Sujud",
    "Duduk di antara dua sujud",
    "Sujud Tilawah",
    "Tasyahud",
    "Shalawat setelah tasyahud (Shalawat Ibrahimiyyah)",
    "Setelah tasyahud akhir sebelum salam",
    "Dzikir Setelah Shalat",

    # 6. Witir
    "Qunut Witir",
    "Setelah salam shalat witir",

    # 7. Doa & Kondisi Hati
    "Do'a memohon petunjuk dalam mengambil keputusan atau memilih jalan yang benar (Istikharah)",
    "Untuk kecemasan dan kesedihan",
    "Bagi orang yang dalam kesusahan",
    "Bagi yang urusannya sulit",
    "Ketika melakukan dosa",
    "Untuk mengusir setan dan bisikannya",
    "Bagi orang yang tertimpa keraguan dalam imannya",

    # 8. Musibah
    "Ketika ditimpa musibah atau didatangi suatu urusan",
    "Bagi yang ditimpa musibah",
    "Doa Pada Waktu Melihat Orang yang Mengalami Cobaan",
    "Ketika melihat seseorang sedang diuji atau ditimpa musibah",

    # 9. Anak
    "Memohon perlindungan Allah untuk anak-anak",

    # 10. Sakit & Kematian
    "Ketika menjenguk orang sakit",
    "Keutamaan menjenguk orang sakit",
    "Ketika orang yang sakit telah berputus asa dari kesembuhan",
    "Petunjuk bagi yang akan meninggal",
    "Saat memejamkan mata jenazah",
    "Bagi jenazah saat salat jenazah",
    "Saat jenazah adalah anak kecil, dalam salat jenazah",
    "Doa Untuk Ta’ziyah (Belasungkawa)",
    "Meletakkan jenazah di liang lahat",
    "Setelah mengubur jenazah",
    "Saat mengunjungi kuburan",

    # 11. Alam
    "Saat badai angin",
    "Ketika mendengar guntur",
    "Agar hujan turun",
    "Ketika hujan turun",
    "Setelah hujan turun",
    "Memohon langit cerah",
    "Ketika melihat bulan sabit",

    # 12. Puasa & Makan
    "Ketika berbuka puasa",
    "Sebelum makan",
    "Setelah selesai makan",
    "Ketika dihina saat berpuasa",
    "Untuk orang yang berpuasa ketika disuguhkan makanan dan tidak membatalkan puasanya",
    "Saat berbuka puasa di rumah seseorang",

    # 13. Sosial
    "Tamu untuk tuan rumah",
    "Kepada orang yang menawarkan minuman atau kepada orang yang berniat melakukannya",
    "Ketika bersin",
    "Ketika orang yang tidak beriman memuji Allah setelah bersin",
    "Kepada orang yang berbuat baik kepadamu",
    "Kepada orang yang menyatakan cintanya kepadamu karena Allah",
    "Kepada orang yang telah menawarimu sebagian hartanya",
    "Untuk orang yang berutang ketika utangnya telah dilunasi",
    "Bagi orang yang Anda hina",
    "Bagi orang yang telah dipuji",
    "Pada suatu majelis atau perkumpulan",
    "Untuk penghapusan dosa, diucapkan pada penutup majelis atau perkumpulan",

    # 14. Pernikahan
    "Kepada pengantin baru",
    "Doa Pengantin pria kepada Istrinya, atau ketika membeli binatang ternak",
    "Sebelum berhubungan seksual",

    # 15. Akhlak
    "Ketika marah",

    # 16. Hutang
    "Melunasi hutang",

    # 17. Safar
    "Ketika keluar dari rumah",
    "Ketika masuk ke rumah",
    "Ketika menaiki binatang tunggangan atau kendaraan apa pun",
    "Untuk bepergian",
    "Doa Musafir kepada Orang yang Dia Tinggalkan",
    "Doa Orang yang Mukim kepada Orang yang Akan Bepergian",
    "Ketika memasuki kota atau desa",
    "Ketika memasuki pasar",
    "Dzikir saat naik atau turun",
    "Doa musafir menjelang subuh",
    "Saat berhenti atau bermalam di suatu tempat",
    "Ketika binatang tunggangan (atau kendaraan) tergelincir",

    # 18. Konflik
    "Ketika menghadapi musuh atau pihak yang berkuasa",
    "Melawan musuh",
    "Ketika takut akan sekelompok orang",
    "Bagi orang yang takut akan ketidakadilan penguasa",

    # 19. Berita
    "Apa yang diucapkan ketika menerima berita yang menyenangkan atau tidak menyenangkan",
    "Ketika menerima kabar baik",

    # 20. Hewan
    "Saat mendengar kokok ayam jantan atau ringkikan keledai",

    # 21. Haji & Umrah
    "Talbiyah bagi yang sedang Haji atau Umrah",
    "Takbir melewati batu hitam",
    "Di antara rukun Yamani dan batu hitam",
    "Ketika di Bukit Safa dan Bukit Marwah",
    "Hari Arafah",
    "Ketika melempar jumrah",

    # 22. Lain-lain
    "Ketika melihat buah yang masih muda atau belum matang",
    "Ketika merasakan sedikit sakit di badan",
    "Ketika khawatir menimpa sesuatu atau seseorang dengan pandangannya",
    "Ketika menyembelih atau mempersembahkan kurban",
]

# Build index for fast lookup
order_index = {name: i for i, name in enumerate(ORDER)}

def get_bahasa_title(item):
    for n in item.get("name", []):
        if n.get("language") == "bahasa":
            return n.get("text", "").strip()
    return None

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

matched = []
unmatched = []

for item in data:
    title = get_bahasa_title(item)
    if title in order_index:
        matched.append((order_index[title], item))
    else:
        unmatched.append(item)

# Sort matched items by canonical order
matched.sort(key=lambda x: x[0])

# Final ordered list
ordered_data = [item for _, item in matched] + unmatched

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(ordered_data, f, ensure_ascii=False, indent=2)

print(f"Reordering complete: {len(matched)} ordered, {len(unmatched)} appended.")