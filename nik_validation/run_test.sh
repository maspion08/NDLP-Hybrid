#!/bin/bash
# ================================================
# Validasi 100 NIK VALID terhadap sistem NDLP
# Dijalankan di VM_CLIENT setelah mitmdump aktif
# ================================================

TARGET="https://192.168.2.10/api/data"
LOG="validation_results.log"
echo "=== Mulai validasi 100 NIK valid pada $(date) ===" > $LOG

echo "--- Test 001 (json_simple) | NIK expected: 1841652010749119 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Siti Rahayu","nik":"1841652010749119","phone":"08218813998"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 002 (json_nested) | NIK expected: 7374714808970042 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7374714808970042","nama":"Rizki Aditya"},"kontak":{"telepon":"08969879730"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 003 (form) | NIK expected: 1615372701888033 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Maya Anggraini&nik=1615372701888033&telepon=08121417075' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 004 (naratif) | NIK expected: 6227516606826167 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Dewi Lestari dengan NIK 6227516606826167 dan nomor telepon 08524556815 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 005 (json_simple) | NIK expected: 9182105809654787 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Siti Rahayu","nik":"9182105809654787","phone":"08568447294"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 006 (json_nested) | NIK expected: 5359195212615957 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"5359195212615957","nama":"Budi Santoso"},"kontak":{"telepon":"08965576169"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 007 (form) | NIK expected: 7655125609971908 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Andi Saputra&nik=7655125609971908&telepon=08521689768' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 008 (naratif) | NIK expected: 7465974909856881 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Hendra Pratama dengan NIK 7465974909856881 dan nomor telepon 08966978809 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 009 (json_simple) | NIK expected: 8166672504962114 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Dewi Lestari","nik":"8166672504962114","phone":"08962081967"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 010 (json_nested) | NIK expected: 1491671410057702 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1491671410057702","nama":"Agus Wijaya"},"kontak":{"telepon":"08523177848"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 011 (form) | NIK expected: 2162301512007691 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Rizki Aditya&nik=2162301512007691&telepon=08774887663' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 012 (naratif) | NIK expected: 5172525711957847 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Hendra Pratama dengan NIK 5172525711957847 dan nomor telepon 08964002978 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 013 (json_simple) | NIK expected: 7256264201772456 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Putri Maharani","nik":"7256264201772456","phone":"08213477876"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 014 (json_nested) | NIK expected: 7667636305727956 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7667636305727956","nama":"Andi Saputra"},"kontak":{"telepon":"08770457178"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 015 (form) | NIK expected: 7666996209870551 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Hendra Pratama&nik=7666996209870551&telepon=08522671475' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 016 (naratif) | NIK expected: 5341592312888441 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Siti Rahayu dengan NIK 5341592312888441 dan nomor telepon 08136270107 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 017 (json_simple) | NIK expected: 5158246102904366 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Maya Anggraini","nik":"5158246102904366","phone":"08561933190"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 018 (json_nested) | NIK expected: 8248131503860230 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"8248131503860230","nama":"Andi Saputra"},"kontak":{"telepon":"08215205997"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 019 (form) | NIK expected: 1601580804991980 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Agus Wijaya&nik=1601580804991980&telepon=08563792984' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 020 (naratif) | NIK expected: 1397705211022536 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Siti Rahayu dengan NIK 1397705211022536 dan nomor telepon 08522294866 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 021 (json_simple) | NIK expected: 1141867112042210 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Agus Wijaya","nik":"1141867112042210","phone":"08563601610"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 022 (json_nested) | NIK expected: 3561761712984763 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3561761712984763","nama":"Ratna Sari"},"kontak":{"telepon":"08775008754"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 023 (form) | NIK expected: 1654861010688319 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Putri Maharani&nik=1654861010688319&telepon=08211779922' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 024 (naratif) | NIK expected: 7350203101841739 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Maya Anggraini dengan NIK 7350203101841739 dan nomor telepon 08563695793 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 025 (json_simple) | NIK expected: 7110077006010423 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Siti Rahayu","nik":"7110077006010423","phone":"08566032080"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 026 (json_nested) | NIK expected: 1266615505035342 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1266615505035342","nama":"Putri Maharani"},"kontak":{"telepon":"08963702838"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 027 (form) | NIK expected: 1864601710693392 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Agus Wijaya&nik=1864601710693392&telepon=08132646861' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 028 (naratif) | NIK expected: 7480446204981139 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Rizki Aditya dengan NIK 7480446204981139 dan nomor telepon 08212524776 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 029 (json_simple) | NIK expected: 7205261811620790 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Hendra Pratama","nik":"7205261811620790","phone":"08522587718"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 030 (json_nested) | NIK expected: 7597832212900336 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7597832212900336","nama":"Andi Saputra"},"kontak":{"telepon":"08964133017"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 031 (form) | NIK expected: 1983680603933048 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Ratna Sari&nik=1983680603933048&telepon=08528205258' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 032 (naratif) | NIK expected: 7135555007653068 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Maya Anggraini dengan NIK 7135555007653068 dan nomor telepon 08968319489 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 033 (json_simple) | NIK expected: 6423345007917663 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Dewi Lestari","nik":"6423345007917663","phone":"08564948214"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 034 (json_nested) | NIK expected: 3242675702888597 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3242675702888597","nama":"Siti Rahayu"},"kontak":{"telepon":"08522105218"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 035 (form) | NIK expected: 5213282902607441 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Ratna Sari&nik=5213282902607441&telepon=08219145244' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 036 (naratif) | NIK expected: 6353702806612569 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Siti Rahayu dengan NIK 6353702806612569 dan nomor telepon 08126460013 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 037 (json_simple) | NIK expected: 6472882310674596 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Budi Santoso","nik":"6472882310674596","phone":"08211189557"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 038 (json_nested) | NIK expected: 3473384509021663 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3473384509021663","nama":"Maya Anggraini"},"kontak":{"telepon":"08779065939"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 039 (form) | NIK expected: 5113560211665837 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Putri Maharani&nik=5113560211665837&telepon=08521584645' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 040 (naratif) | NIK expected: 3283810906929636 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Budi Santoso dengan NIK 3283810906929636 dan nomor telepon 08776045414 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 041 (json_simple) | NIK expected: 1538410305760228 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Rizki Aditya","nik":"1538410305760228","phone":"08219085380"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 042 (json_nested) | NIK expected: 7333540802630377 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7333540802630377","nama":"Siti Rahayu"},"kontak":{"telepon":"08139110285"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 043 (form) | NIK expected: 6116136008800623 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Maya Anggraini&nik=6116136008800623&telepon=08774069256' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 044 (naratif) | NIK expected: 7241781408981957 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Rizki Aditya dengan NIK 7241781408981957 dan nomor telepon 08523632280 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 045 (json_simple) | NIK expected: 6565887105845838 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Andi Saputra","nik":"6565887105845838","phone":"08778642300"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 046 (json_nested) | NIK expected: 1495926305615416 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1495926305615416","nama":"Hendra Pratama"},"kontak":{"telepon":"08567645291"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 047 (form) | NIK expected: 5394991107799595 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Agus Wijaya&nik=5394991107799595&telepon=08560845850' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 048 (naratif) | NIK expected: 1270442401951845 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Budi Santoso dengan NIK 1270442401951845 dan nomor telepon 08773703826 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 049 (json_simple) | NIK expected: 3180161703625801 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Ratna Sari","nik":"3180161703625801","phone":"08963845355"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 050 (json_nested) | NIK expected: 6104551307826180 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"6104551307826180","nama":"Putri Maharani"},"kontak":{"telepon":"08777879432"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 051 (form) | NIK expected: 3654851803680466 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Rizki Aditya&nik=3654851803680466&telepon=08137058602' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 052 (naratif) | NIK expected: 7233190901618867 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Siti Rahayu dengan NIK 7233190901618867 dan nomor telepon 08215842108 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 053 (json_simple) | NIK expected: 8154345911681466 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Dewi Lestari","nik":"8154345911681466","phone":"08969490668"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 054 (json_nested) | NIK expected: 3271055711815202 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3271055711815202","nama":"Andi Saputra"},"kontak":{"telepon":"08962811265"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 055 (form) | NIK expected: 1485020801908334 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Andi Saputra&nik=1485020801908334&telepon=08214093244' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 056 (naratif) | NIK expected: 2196526709744519 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Andi Saputra dengan NIK 2196526709744519 dan nomor telepon 08215263097 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 057 (json_simple) | NIK expected: 6326485511898992 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Rizki Aditya","nik":"6326485511898992","phone":"08218280258"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 058 (json_nested) | NIK expected: 8187756103726727 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"8187756103726727","nama":"Agus Wijaya"},"kontak":{"telepon":"08130180515"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 059 (form) | NIK expected: 2163015412930615 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Hendra Pratama&nik=2163015412930615&telepon=08138299321' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 060 (naratif) | NIK expected: 3211394912942261 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Ratna Sari dengan NIK 3211394912942261 dan nomor telepon 08521164941 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 061 (json_simple) | NIK expected: 1703691010049382 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Ratna Sari","nik":"1703691010049382","phone":"08527188357"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 062 (json_nested) | NIK expected: 1351490302922325 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1351490302922325","nama":"Maya Anggraini"},"kontak":{"telepon":"08211117443"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 063 (form) | NIK expected: 7143716401799712 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Agus Wijaya&nik=7143716401799712&telepon=08216885576' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 064 (naratif) | NIK expected: 3321385205942196 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Ratna Sari dengan NIK 3321385205942196 dan nomor telepon 08133735569 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 065 (json_simple) | NIK expected: 7125961611986925 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Rizki Aditya","nik":"7125961611986925","phone":"08132792645"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 066 (json_nested) | NIK expected: 6499690601935156 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"6499690601935156","nama":"Siti Rahayu"},"kontak":{"telepon":"08214742843"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 067 (form) | NIK expected: 2121042911920033 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Ratna Sari&nik=2121042911920033&telepon=08138144976' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 068 (naratif) | NIK expected: 6509484509739823 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Rizki Aditya dengan NIK 6509484509739823 dan nomor telepon 08128565178 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 069 (json_simple) | NIK expected: 3617146802911199 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Andi Saputra","nik":"3617146802911199","phone":"08136550620"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 070 (json_nested) | NIK expected: 7134795202017773 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7134795202017773","nama":"Hendra Pratama"},"kontak":{"telepon":"08564259967"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 071 (form) | NIK expected: 8216722711827471 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Putri Maharani&nik=8216722711827471&telepon=08210031450' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 072 (naratif) | NIK expected: 6411090905913704 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Dewi Lestari dengan NIK 6411090905913704 dan nomor telepon 08967849518 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 073 (json_simple) | NIK expected: 3142566212808081 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Dewi Lestari","nik":"3142566212808081","phone":"08560125373"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 074 (json_nested) | NIK expected: 7241232804895711 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"7241232804895711","nama":"Maya Anggraini"},"kontak":{"telepon":"08772419689"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 075 (form) | NIK expected: 6453765503739283 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Andi Saputra&nik=6453765503739283&telepon=08131046028' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 076 (naratif) | NIK expected: 1956354906677282 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Andi Saputra dengan NIK 1956354906677282 dan nomor telepon 08137555597 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 077 (json_simple) | NIK expected: 5119704506749197 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Hendra Pratama","nik":"5119704506749197","phone":"08525407207"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 078 (json_nested) | NIK expected: 1835385307000356 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1835385307000356","nama":"Ratna Sari"},"kontak":{"telepon":"08217354864"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 079 (form) | NIK expected: 6387536511668105 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Dewi Lestari&nik=6387536511668105&telepon=08560618847' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 080 (naratif) | NIK expected: 9427554206016550 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Maya Anggraini dengan NIK 9427554206016550 dan nomor telepon 08128895755 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 081 (json_simple) | NIK expected: 3202355906686794 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Ratna Sari","nik":"3202355906686794","phone":"08131824886"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 082 (json_nested) | NIK expected: 8162442104621980 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"8162442104621980","nama":"Siti Rahayu"},"kontak":{"telepon":"08563073368"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 083 (form) | NIK expected: 5242030909896053 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Andi Saputra&nik=5242030909896053&telepon=08138347285' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 084 (naratif) | NIK expected: 1672890401942554 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Ratna Sari dengan NIK 1672890401942554 dan nomor telepon 08776898329 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 085 (json_simple) | NIK expected: 6329600611985070 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Andi Saputra","nik":"6329600611985070","phone":"08772229004"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 086 (json_nested) | NIK expected: 1673540901666874 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"1673540901666874","nama":"Hendra Pratama"},"kontak":{"telepon":"08962248527"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 087 (form) | NIK expected: 1324712211905592 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Agus Wijaya&nik=1324712211905592&telepon=08130226978' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 088 (naratif) | NIK expected: 6345416908765359 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Budi Santoso dengan NIK 6345416908765359 dan nomor telepon 08213858176 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 089 (json_simple) | NIK expected: 5105835601686000 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Agus Wijaya","nik":"5105835601686000","phone":"08212807001"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 090 (json_nested) | NIK expected: 5197601705836553 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"5197601705836553","nama":"Ratna Sari"},"kontak":{"telepon":"08564502831"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 091 (form) | NIK expected: 6128752402868339 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Rizki Aditya&nik=6128752402868339&telepon=08776323373' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 092 (naratif) | NIK expected: 6162792009925327 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Ratna Sari dengan NIK 6162792009925327 dan nomor telepon 08138667534 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 093 (json_simple) | NIK expected: 8241854303839209 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Putri Maharani","nik":"8241854303839209","phone":"08569713311"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 094 (json_nested) | NIK expected: 3298336002003520 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3298336002003520","nama":"Ratna Sari"},"kontak":{"telepon":"08779212363"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 095 (form) | NIK expected: 1260312809878628 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Rizki Aditya&nik=1260312809878628&telepon=08128244560' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 096 (naratif) | NIK expected: 1966284508059157 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Putri Maharani dengan NIK 1966284508059157 dan nomor telepon 08567457212 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 097 (json_simple) | NIK expected: 6247846410948833 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"nama":"Andi Saputra","nik":"6247846410948833","phone":"08135769908"}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 098 (json_nested) | NIK expected: 3320782603699388 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/json" \
     -d '{"data":{"identitas":{"nik":"3320782603699388","nama":"Ratna Sari"},"kontak":{"telepon":"08964177588"}}}' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 099 (form) | NIK expected: 1486054503794384 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'nama=Andi Saputra&nik=1486054503794384&telepon=08124401901' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "--- Test 100 (naratif) | NIK expected: 6417590212713042 ---" >> $LOG
curl -k -s -o /dev/null -w 'HTTP: %{http_code} | Time: %{time_total}s\n' \
     -X POST "$TARGET" \
     -H "Content-Type: text/plain" \
     -d 'Saudara Andi Saputra dengan NIK 6417590212713042 dan nomor telepon 08529169797 telah terdaftar.' >> $LOG
sleep 0.1   # spasi antar request agar mitmdump tidak terbebani

echo "=== Selesai pada $(date) ===" >> $LOG
echo "Total: 100 permintaan dikirim. Lihat $LOG untuk hasilnya."