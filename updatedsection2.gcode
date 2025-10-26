; Cleaning G-code for Carousel - bottom: section 2
; Reference points are:
;   pt1 the left bottom outside corner of S2 pad 16
;   pt2 the left bottom corner of the S2 pad 8
;   pt3 the right bottom outside corner of S2 pad 1
; reference_point1 = (-179.6534, -83.904)
; reference_point2 = (7.0425, -173.9554)
; reference_point3 = (179.6534, -83.904)
G90 ; absolute coordinates
G21 ; metric units
G17 ; arcs in XY plane
M4 S10000
G0 X0.0000 Y0.0000 Z0.0000
G0 X188.7140 Y-71.0950
G1 X186.4780 Y-74.5120 F500 ; pad 2-1, offset 0.1
G1 X184.2340 Y-77.8080 F500 ; arch to point 2
G1 X181.9320 Y-81.0630 F500 ; arch to point 2
G1 X179.5150 Y-84.3550 F500 ; arch to point 2
G1 X170.8380 Y-78.3350 F500 ; side move pt 2 to pt 3
G1 X173.2610 Y-75.0430 F500 ; arch to pt 4
G1 X175.5620 Y-71.7920 F500 ; arch to pt 4
G1 X177.8020 Y-68.4980 F500 ; arch to pt 4
G1 X180.0370 Y-65.0750 F500 ; arch to pt 4
G1 X188.7140 Y-71.0950 F500 ; move to pt1
G0 X188.8240 Y-71.0740
G1 X186.5440 Y-74.5560 F500 ; pad 2-1, offset 0.18
G1 X184.3000 Y-77.8530 F500 ; arch to point 2
G1 X181.9980 Y-81.1100 F500 ; arch to point 2
G1 X179.5340 Y-84.4650 F500 ; arch to point 2
G1 X170.7250 Y-78.3540 F500 ; side move pt 2 to pt 3
G1 X173.1960 Y-74.9970 F500 ; arch to pt 4
G1 X175.4960 Y-71.7460 F500 ; arch to pt 4
G1 X177.7360 Y-68.4530 F500 ; arch to pt 4
G1 X180.0150 Y-64.9630 F500 ; arch to pt 4
G1 X188.8240 Y-71.0740 F500 ; move to pt1
G0 X188.9330 Y-71.0520
G1 X186.6110 Y-74.6000 F500 ; pad 2-1, offset 0.26
G1 X184.3650 Y-77.8990 F500 ; arch to point 2
G1 X182.0620 Y-81.1570 F500 ; arch to point 2
G1 X179.5520 Y-84.5750 F500 ; arch to point 2
G1 X170.6120 Y-78.3730 F500 ; side move pt 2 to pt 3
G1 X173.1320 Y-74.9500 F500 ; arch to pt 4
G1 X175.4310 Y-71.7010 F500 ; arch to pt 4
G1 X177.6690 Y-68.4090 F500 ; arch to pt 4
G1 X179.9930 Y-64.8500 F500 ; arch to pt 4
G1 X188.9330 Y-71.0520 F500 ; move to pt1
G0 X189.0430 Y-71.0310
G1 X186.6770 Y-74.6450 F500 ; pad 2-1, offset 0.34
G1 X184.4310 Y-77.9440 F500 ; arch to point 2
G1 X182.1270 Y-81.2040 F500 ; arch to point 2
G1 X179.5710 Y-84.6850 F500 ; arch to point 2
G1 X170.4980 Y-78.3910 F500 ; side move pt 2 to pt 3
G1 X173.0670 Y-74.9030 F500 ; arch to pt 4
G1 X175.3650 Y-71.6550 F500 ; arch to pt 4
G1 X177.6030 Y-68.3650 F500 ; arch to pt 4
G1 X179.9700 Y-64.7370 F500 ; arch to pt 4
G1 X189.0430 Y-71.0310 F500 ; move to pt1
G0 X189.1530 Y-71.0100
G1 X186.7430 Y-74.6900 F500 ; pad 2-1, offset 0.42
G1 X184.4970 Y-77.9900 F500 ; arch to point 2
G1 X182.1930 Y-81.2500 F500 ; arch to point 2
G1 X179.5890 Y-84.7960 F500 ; arch to point 2
G1 X170.3850 Y-78.4100 F500 ; side move pt 2 to pt 3
G1 X173.0020 Y-74.8560 F500 ; arch to pt 4
G1 X175.2990 Y-71.6090 F500 ; arch to pt 4
G1 X177.5360 Y-68.3210 F500 ; arch to pt 4
G1 X179.9490 Y-64.6250 F500 ; arch to pt 4
G1 X189.1530 Y-71.0100 F500 ; move to pt1
G0 X173.7930 Y-91.6800
G1 X171.1840 Y-94.8210 F500 ; pad 2-2, offset 0.1
G1 X168.5810 Y-97.8420 F500 ; arch to point 2
G1 X165.9260 Y-100.8160 F500 ; arch to point 2
G1 X163.1520 Y-103.8130 F500 ; arch to point 2
G1 X155.2120 Y-96.8490 F500 ; side move pt 2 to pt 3
G1 X157.9920 Y-93.8530 F500 ; arch to pt 4
G1 X160.6460 Y-90.8830 F500 ; arch to pt 4
G1 X163.2450 Y-87.8640 F500 ; arch to pt 4
G1 X165.8520 Y-84.7160 F500 ; arch to pt 4
G1 X173.7930 Y-91.6800 F500 ; move to pt1
G0 X173.9040 Y-91.6710
G1 X171.2450 Y-94.8730 F500 ; pad 2-2, offset 0.18
G1 X168.6410 Y-97.8950 F500 ; arch to point 2
G1 X165.9860 Y-100.8700 F500 ; arch to point 2
G1 X163.1580 Y-103.9240 F500 ; arch to point 2
G1 X155.0970 Y-96.8560 F500 ; side move pt 2 to pt 3
G1 X157.9330 Y-93.8000 F500 ; arch to pt 4
G1 X160.5860 Y-90.8300 F500 ; arch to pt 4
G1 X163.1840 Y-87.8120 F500 ; arch to pt 4
G1 X165.8430 Y-84.6020 F500 ; arch to pt 4
G1 X173.9040 Y-91.6710 F500 ; move to pt1
G0 X174.0150 Y-91.6620
G1 X171.3060 Y-94.9240 F500 ; pad 2-2, offset 0.26
G1 X168.7020 Y-97.9470 F500 ; arch to point 2
G1 X166.0440 Y-100.9240 F500 ; arch to point 2
G1 X163.1640 Y-104.0360 F500 ; arch to point 2
G1 X154.9830 Y-96.8620 F500 ; side move pt 2 to pt 3
G1 X157.8740 Y-93.7460 F500 ; arch to pt 4
G1 X160.5260 Y-90.7780 F500 ; arch to pt 4
G1 X163.1220 Y-87.7610 F500 ; arch to pt 4
G1 X165.8350 Y-84.4880 F500 ; arch to pt 4
G1 X174.0150 Y-91.6620 F500 ; move to pt1
G0 X174.1270 Y-91.6530
G1 X171.3670 Y-94.9760 F500 ; pad 2-2, offset 0.34
G1 X168.7620 Y-98.0000 F500 ; arch to point 2
G1 X166.1040 Y-100.9780 F500 ; arch to point 2
G1 X163.1700 Y-104.1480 F500 ; arch to point 2
G1 X154.8680 Y-96.8670 F500 ; side move pt 2 to pt 3
G1 X157.8150 Y-93.6920 F500 ; arch to pt 4
G1 X160.4660 Y-90.7250 F500 ; arch to pt 4
G1 X163.0620 Y-87.7090 F500 ; arch to pt 4
G1 X165.8250 Y-84.3730 F500 ; arch to pt 4
G1 X174.1270 Y-91.6530 F500 ; move to pt1
G0 X174.2380 Y-91.6450
G1 X171.4280 Y-95.0280 F500 ; pad 2-2, offset 0.42
G1 X168.8220 Y-98.0530 F500 ; arch to point 2
G1 X166.1630 Y-101.0310 F500 ; arch to point 2
G1 X163.1760 Y-104.2590 F500 ; arch to point 2
G1 X154.7530 Y-96.8730 F500 ; side move pt 2 to pt 3
G1 X157.7560 Y-93.6380 F500 ; arch to pt 4
G1 X160.4060 Y-90.6720 F500 ; arch to pt 4
G1 X163.0000 Y-87.6580 F500 ; arch to pt 4
G1 X165.8160 Y-84.2590 F500 ; arch to pt 4
G1 X174.2380 Y-91.6450 F500 ; move to pt1
G0 X153.8130 Y-113.1520
G1 X150.8160 Y-115.9260 F500 ; pad 2-3, offset 0.1
G1 X147.8420 Y-118.5810 F500 ; arch to point 2
G1 X144.8210 Y-121.1840 F500 ; arch to point 2
G1 X141.6800 Y-123.7930 F500 ; arch to point 2
G1 X134.7160 Y-115.8520 F500 ; side move pt 2 to pt 3
G1 X137.8640 Y-113.2450 F500 ; arch to pt 4
G1 X140.8830 Y-110.6460 F500 ; arch to pt 4
G1 X143.8530 Y-107.9920 F500 ; arch to pt 4
G1 X146.8490 Y-105.2120 F500 ; arch to pt 4
G1 X153.8130 Y-113.1520 F500 ; move to pt1
G0 X153.9240 Y-113.1580
G1 X150.8700 Y-115.9860 F500 ; pad 2-3, offset 0.18
G1 X147.8950 Y-118.6410 F500 ; arch to point 2
G1 X144.8730 Y-121.2450 F500 ; arch to point 2
G1 X141.6710 Y-123.9040 F500 ; arch to point 2
G1 X134.6020 Y-115.8430 F500 ; side move pt 2 to pt 3
G1 X137.8120 Y-113.1840 F500 ; arch to pt 4
G1 X140.8300 Y-110.5860 F500 ; arch to pt 4
G1 X143.8000 Y-107.9330 F500 ; arch to pt 4
G1 X146.8560 Y-105.0970 F500 ; arch to pt 4
G1 X153.9240 Y-113.1580 F500 ; move to pt1
G0 X154.0360 Y-113.1640
G1 X150.9240 Y-116.0440 F500 ; pad 2-3, offset 0.26
G1 X147.9470 Y-118.7020 F500 ; arch to point 2
G1 X144.9240 Y-121.3060 F500 ; arch to point 2
G1 X141.6620 Y-124.0150 F500 ; arch to point 2
G1 X134.4880 Y-115.8350 F500 ; side move pt 2 to pt 3
G1 X137.7610 Y-113.1220 F500 ; arch to pt 4
G1 X140.7780 Y-110.5260 F500 ; arch to pt 4
G1 X143.7460 Y-107.8740 F500 ; arch to pt 4
G1 X146.8620 Y-104.9830 F500 ; arch to pt 4
G1 X154.0360 Y-113.1640 F500 ; move to pt1
G0 X154.1480 Y-113.1700
G1 X150.9780 Y-116.1040 F500 ; pad 2-3, offset 0.34
G1 X148.0000 Y-118.7620 F500 ; arch to point 2
G1 X144.9760 Y-121.3670 F500 ; arch to point 2
G1 X141.6530 Y-124.1270 F500 ; arch to point 2
G1 X134.3730 Y-115.8250 F500 ; side move pt 2 to pt 3
G1 X137.7090 Y-113.0620 F500 ; arch to pt 4
G1 X140.7250 Y-110.4660 F500 ; arch to pt 4
G1 X143.6920 Y-107.8150 F500 ; arch to pt 4
G1 X146.8670 Y-104.8680 F500 ; arch to pt 4
G1 X154.1480 Y-113.1700 F500 ; move to pt1
G0 X154.2590 Y-113.1760
G1 X151.0310 Y-116.1630 F500 ; pad 2-3, offset 0.42
G1 X148.0530 Y-118.8220 F500 ; arch to point 2
G1 X145.0280 Y-121.4280 F500 ; arch to point 2
G1 X141.6450 Y-124.2380 F500 ; arch to point 2
G1 X134.2590 Y-115.8160 F500 ; side move pt 2 to pt 3
G1 X137.6580 Y-113.0000 F500 ; arch to pt 4
G1 X140.6720 Y-110.4060 F500 ; arch to pt 4
G1 X143.6380 Y-107.7560 F500 ; arch to pt 4
G1 X146.8730 Y-104.7530 F500 ; arch to pt 4
G1 X154.2590 Y-113.1760 F500 ; move to pt1
G0 X131.2010 Y-131.8330
G1 X127.8680 Y-134.1920 F500 ; pad 2-4, offset 0.1
G1 X124.5730 Y-136.4360 F500 ; arch to point 2
G1 X121.2380 Y-138.6220 F500 ; arch to point 2
G1 X117.7830 Y-140.7990 F500 ; arch to point 2
G1 X111.9160 Y-132.0170 F500 ; side move pt 2 to pt 3
G1 X115.3770 Y-129.8430 F500 ; arch to pt 4
G1 X118.7090 Y-127.6610 F500 ; arch to pt 4
G1 X122.0000 Y-125.4170 F500 ; arch to pt 4
G1 X125.3340 Y-123.0520 F500 ; arch to pt 4
G1 X131.2010 Y-131.8330 F500 ; move to pt1
G0 X131.3110 Y-131.8530
G1 X127.9140 Y-134.2580 F500 ; pad 2-4, offset 0.18
G1 X124.6170 Y-136.5030 F500 ; arch to point 2
G1 X121.2820 Y-138.6890 F500 ; arch to point 2
G1 X117.7600 Y-140.9080 F500 ; arch to point 2
G1 X111.8040 Y-131.9940 F500 ; side move pt 2 to pt 3
G1 X115.3330 Y-129.7760 F500 ; arch to pt 4
G1 X118.6650 Y-127.5940 F500 ; arch to pt 4
G1 X121.9550 Y-125.3510 F500 ; arch to pt 4
G1 X125.3550 Y-122.9390 F500 ; arch to pt 4
G1 X131.3110 Y-131.8530 F500 ; move to pt1
G0 X131.4210 Y-131.8740
G1 X127.9600 Y-134.3230 F500 ; pad 2-4, offset 0.26
G1 X124.6620 Y-136.5690 F500 ; arch to point 2
G1 X121.3250 Y-138.7570 F500 ; arch to point 2
G1 X117.7370 Y-141.0170 F500 ; arch to point 2
G1 X111.6920 Y-131.9700 F500 ; side move pt 2 to pt 3
G1 X115.2910 Y-129.7080 F500 ; arch to pt 4
G1 X118.6200 Y-127.5280 F500 ; arch to pt 4
G1 X121.9090 Y-125.2860 F500 ; arch to pt 4
G1 X125.3760 Y-122.8260 F500 ; arch to pt 4
G1 X131.4210 Y-131.8740 F500 ; move to pt1
G0 X131.5310 Y-131.8940
G1 X128.0050 Y-134.3890 F500 ; pad 2-4, offset 0.34
G1 X124.7060 Y-136.6360 F500 ; arch to point 2
G1 X121.3680 Y-138.8240 F500 ; arch to point 2
G1 X117.7140 Y-141.1270 F500 ; arch to point 2
G1 X111.5790 Y-131.9450 F500 ; side move pt 2 to pt 3
G1 X115.2470 Y-129.6410 F500 ; arch to pt 4
G1 X118.5760 Y-127.4610 F500 ; arch to pt 4
G1 X121.8640 Y-125.2200 F500 ; arch to pt 4
G1 X125.3960 Y-122.7130 F500 ; arch to pt 4
G1 X131.5310 Y-131.8940 F500 ; move to pt1
G0 X131.6410 Y-131.9140
G1 X128.0500 Y-134.4550 F500 ; pad 2-4, offset 0.42
G1 X124.7510 Y-136.7020 F500 ; arch to point 2
G1 X121.4120 Y-138.8910 F500 ; arch to point 2
G1 X117.6900 Y-141.2360 F500 ; arch to point 2
G1 X111.4670 Y-131.9220 F500 ; side move pt 2 to pt 3
G1 X115.2040 Y-129.5740 F500 ; arch to pt 4
G1 X118.5310 Y-127.3950 F500 ; arch to pt 4
G1 X121.8180 Y-125.1550 F500 ; arch to pt 4
G1 X125.4170 Y-122.6000 F500 ; arch to pt 4
G1 X131.6410 Y-131.9140 F500 ; move to pt1
G0 X106.3450 Y-147.4020
G1 X102.7330 Y-149.3060 F500 ; pad 2-5, offset 0.1
G1 X99.1720 Y-151.1010 F500 ; arch to point 2
G1 X95.5810 Y-152.8330 F500 ; arch to point 2
G1 X91.8710 Y-154.5400 F500 ; arch to point 2
G1 X87.2000 Y-145.0680 F500 ; side move pt 2 to pt 3
G1 X90.9160 Y-143.3640 F500 ; arch to pt 4
G1 X94.5040 Y-141.6360 F500 ; arch to pt 4
G1 X98.0600 Y-139.8410 F500 ; arch to pt 4
G1 X101.6740 Y-137.9310 F500 ; arch to pt 4
G1 X106.3450 Y-147.4020 F500 ; move to pt1
G0 X106.4510 Y-147.4370
G1 X102.7690 Y-149.3780 F500 ; pad 2-5, offset 0.18
G1 X99.2080 Y-151.1730 F500 ; arch to point 2
G1 X95.6150 Y-152.9050 F500 ; arch to point 2
G1 X91.8340 Y-154.6450 F500 ; arch to point 2
G1 X87.0920 Y-145.0300 F500 ; side move pt 2 to pt 3
G1 X90.8810 Y-143.2920 F500 ; arch to pt 4
G1 X94.4690 Y-141.5640 F500 ; arch to pt 4
G1 X98.0240 Y-139.7700 F500 ; arch to pt 4
G1 X101.7090 Y-137.8220 F500 ; arch to pt 4
G1 X106.4510 Y-147.4370 F500 ; move to pt1
G0 X106.5570 Y-147.4720
G1 X102.8060 Y-149.4490 F500 ; pad 2-5, offset 0.26
G1 X99.2430 Y-151.2450 F500 ; arch to point 2
G1 X95.6490 Y-152.9780 F500 ; arch to point 2
G1 X91.7970 Y-154.7510 F500 ; arch to point 2
G1 X86.9840 Y-144.9920 F500 ; side move pt 2 to pt 3
G1 X90.8480 Y-143.2190 F500 ; arch to pt 4
G1 X94.4340 Y-141.4920 F500 ; arch to pt 4
G1 X97.9870 Y-139.6990 F500 ; arch to pt 4
G1 X101.7450 Y-137.7130 F500 ; arch to pt 4
G1 X106.5570 Y-147.4720 F500 ; move to pt1
G0 X106.6640 Y-147.5060
G1 X102.8420 Y-149.5200 F500 ; pad 2-5, offset 0.34
G1 X99.2780 Y-151.3170 F500 ; arch to point 2
G1 X95.6830 Y-153.0500 F500 ; arch to point 2
G1 X91.7590 Y-154.8560 F500 ; arch to point 2
G1 X86.8760 Y-144.9530 F500 ; side move pt 2 to pt 3
G1 X90.8130 Y-143.1470 F500 ; arch to pt 4
G1 X94.3980 Y-141.4200 F500 ; arch to pt 4
G1 X97.9500 Y-139.6270 F500 ; arch to pt 4
G1 X101.7800 Y-137.6030 F500 ; arch to pt 4
G1 X106.6640 Y-147.5060 F500 ; move to pt1
G0 X106.7700 Y-147.5410
G1 X102.8790 Y-149.5910 F500 ; pad 2-5, offset 0.42
G1 X99.3140 Y-151.3880 F500 ; arch to point 2
G1 X95.7180 Y-153.1230 F500 ; arch to point 2
G1 X91.7220 Y-154.9610 F500 ; arch to point 2
G1 X86.7680 Y-144.9150 F500 ; side move pt 2 to pt 3
G1 X90.7800 Y-143.0740 F500 ; arch to pt 4
G1 X94.3630 Y-141.3490 F500 ; arch to pt 4
G1 X97.9130 Y-139.5570 F500 ; arch to pt 4
G1 X101.8150 Y-137.4940 F500 ; arch to pt 4
G1 X106.7700 Y-147.5410 F500 ; move to pt1
G0 X79.6690 Y-159.5940
G1 X75.8390 Y-161.0110 F500 ; pad 2-6, offset 0.1
G1 X72.0750 Y-162.3250 F500 ; arch to point 2
G1 X68.2880 Y-163.5740 F500 ; arch to point 2
G1 X64.3870 Y-164.7820 F500 ; arch to point 2
G1 X60.9930 Y-154.7810 F500 ; side move pt 2 to pt 3
G1 X64.8990 Y-153.5770 F500 ; arch to pt 4
G1 X68.6820 Y-152.3320 F500 ; arch to pt 4
G1 X72.4420 Y-151.0160 F500 ; arch to pt 4
G1 X76.2740 Y-149.5940 F500 ; arch to pt 4
G1 X79.6690 Y-159.5940 F500 ; move to pt1
G0 X79.7700 Y-159.6430
G1 X75.8660 Y-161.0860 F500 ; pad 2-6, offset 0.18
G1 X72.1000 Y-162.4010 F500 ; arch to point 2
G1 X68.3130 Y-163.6500 F500 ; arch to point 2
G1 X64.3370 Y-164.8810 F500 ; arch to point 2
G1 X60.8910 Y-154.7290 F500 ; side move pt 2 to pt 3
G1 X64.8740 Y-153.5010 F500 ; arch to pt 4
G1 X68.6570 Y-152.2560 F500 ; arch to pt 4
G1 X72.4150 Y-150.9410 F500 ; arch to pt 4
G1 X76.3240 Y-149.4910 F500 ; arch to pt 4
G1 X79.7700 Y-159.6430 F500 ; move to pt1
G0 X79.8710 Y-159.6910
G1 X75.8930 Y-161.1610 F500 ; pad 2-6, offset 0.26
G1 X72.1260 Y-162.4770 F500 ; arch to point 2
G1 X68.3370 Y-163.7260 F500 ; arch to point 2
G1 X64.2860 Y-164.9810 F500 ; arch to point 2
G1 X60.7880 Y-154.6770 F500 ; side move pt 2 to pt 3
G1 X64.8500 Y-153.4240 F500 ; arch to pt 4
G1 X68.6310 Y-152.1800 F500 ; arch to pt 4
G1 X72.3880 Y-150.8660 F500 ; arch to pt 4
G1 X76.3730 Y-149.3870 F500 ; arch to pt 4
G1 X79.8710 Y-159.6910 F500 ; move to pt1
G0 X79.9710 Y-159.7390
G1 X75.9200 Y-161.2370 F500 ; pad 2-6, offset 0.34
G1 X72.1520 Y-162.5530 F500 ; arch to point 2
G1 X68.3610 Y-163.8020 F500 ; arch to point 2
G1 X64.2350 Y-165.0810 F500 ; arch to point 2
G1 X60.6860 Y-154.6250 F500 ; side move pt 2 to pt 3
G1 X64.8250 Y-153.3480 F500 ; arch to pt 4
G1 X68.6050 Y-152.1040 F500 ; arch to pt 4
G1 X72.3610 Y-150.7900 F500 ; arch to pt 4
G1 X76.4220 Y-149.2830 F500 ; arch to pt 4
G1 X79.9710 Y-159.7390 F500 ; move to pt1
G0 X80.0720 Y-159.7870
G1 X75.9470 Y-161.3120 F500 ; pad 2-6, offset 0.42
G1 X72.1780 Y-162.6280 F500 ; arch to point 2
G1 X68.3860 Y-163.8780 F500 ; arch to point 2
G1 X64.1850 Y-165.1800 F500 ; arch to point 2
G1 X60.5840 Y-154.5730 F500 ; side move pt 2 to pt 3
G1 X64.8020 Y-153.2720 F500 ; arch to pt 4
G1 X68.5790 Y-152.0280 F500 ; arch to pt 4
G1 X72.3330 Y-150.7150 F500 ; arch to pt 4
G1 X76.4710 Y-149.1790 F500 ; arch to pt 4
G1 X80.0720 Y-159.7870 F500 ; move to pt1
G0 X51.6300 Y-168.2000
G1 X47.6480 Y-169.1040 F500 ; pad 2-7, offset 0.1
G1 X43.7440 Y-169.9170 F500 ; arch to point 2
G1 X39.8270 Y-170.6600 F500 ; arch to point 2
G1 X35.8020 Y-171.3490 F500 ; arch to point 2
G1 X33.7420 Y-160.9900 F500 ; side move pt 2 to pt 3
G1 X37.7710 Y-160.3060 F500 ; arch to pt 4
G1 X41.6850 Y-159.5650 F500 ; arch to pt 4
G1 X45.5840 Y-158.7520 F500 ; arch to pt 4
G1 X49.5690 Y-157.8420 F500 ; arch to pt 4
G1 X51.6300 Y-168.2000 F500 ; move to pt1
G0 X51.7230 Y-168.2610
G1 X47.6640 Y-169.1830 F500 ; pad 2-7, offset 0.18
G1 X43.7600 Y-169.9950 F500 ; arch to point 2
G1 X39.8420 Y-170.7390 F500 ; arch to point 2
G1 X35.7390 Y-171.4410 F500 ; arch to point 2
G1 X33.6470 Y-160.9260 F500 ; side move pt 2 to pt 3
G1 X37.7570 Y-160.2270 F500 ; arch to pt 4
G1 X41.6700 Y-159.4870 F500 ; arch to pt 4
G1 X45.5680 Y-158.6740 F500 ; arch to pt 4
G1 X49.6320 Y-157.7460 F500 ; arch to pt 4
G1 X51.7230 Y-168.2610 F500 ; move to pt1
G0 X51.8170 Y-168.3220
G1 X47.6820 Y-169.2610 F500 ; pad 2-7, offset 0.26
G1 X43.7750 Y-170.0740 F500 ; arch to point 2
G1 X39.8550 Y-170.8180 F500 ; arch to point 2
G1 X35.6750 Y-171.5330 F500 ; arch to point 2
G1 X33.5530 Y-160.8610 F500 ; side move pt 2 to pt 3
G1 X37.7430 Y-160.1490 F500 ; arch to pt 4
G1 X41.6540 Y-159.4080 F500 ; arch to pt 4
G1 X45.5500 Y-158.5960 F500 ; arch to pt 4
G1 X49.6940 Y-157.6500 F500 ; arch to pt 4
G1 X51.8170 Y-168.3220 F500 ; move to pt1
G0 X51.9110 Y-168.3830
G1 X47.6980 Y-169.3390 F500 ; pad 2-7, offset 0.34
G1 X43.7910 Y-170.1520 F500 ; arch to point 2
G1 X39.8700 Y-170.8960 F500 ; arch to point 2
G1 X35.6120 Y-171.6250 F500 ; arch to point 2
G1 X33.4580 Y-160.7950 F500 ; side move pt 2 to pt 3
G1 X37.7290 Y-160.0700 F500 ; arch to pt 4
G1 X41.6380 Y-159.3300 F500 ; arch to pt 4
G1 X45.5340 Y-158.5170 F500 ; arch to pt 4
G1 X49.7570 Y-157.5530 F500 ; arch to pt 4
G1 X51.9110 Y-168.3830 F500 ; move to pt1
G0 X52.0050 Y-168.4440
G1 X47.7150 Y-169.4170 F500 ; pad 2-7, offset 0.42
G1 X43.8070 Y-170.2300 F500 ; arch to point 2
G1 X39.8840 Y-170.9750 F500 ; arch to point 2
G1 X35.5490 Y-171.7170 F500 ; arch to point 2
G1 X33.3630 Y-160.7300 F500 ; side move pt 2 to pt 3
G1 X37.7150 Y-159.9910 F500 ; arch to pt 4
G1 X41.6230 Y-159.2520 F500 ; arch to pt 4
G1 X45.5160 Y-158.4390 F500 ; arch to pt 4
G1 X49.8190 Y-157.4570 F500 ; arch to pt 4
G1 X52.0050 Y-168.4440 F500 ; move to pt1
G0 X22.7070 Y-173.0720
G1 X18.6410 Y-173.4490 F500 ; pad 2-8, offset 0.1
G1 X14.6650 Y-173.7450 F500 ; arch to point 2
G1 X10.6840 Y-173.9710 F500 ; arch to point 2
G1 X6.6040 Y-174.1280 F500 ; arch to point 2
G1 X5.9130 Y-163.5900 F500 ; side move pt 2 to pt 3
G1 X9.9980 Y-163.4370 F500 ; arch to pt 4
G1 X13.9750 Y-163.2140 F500 ; arch to pt 4
G1 X17.9470 Y-162.9160 F500 ; arch to pt 4
G1 X22.0170 Y-162.5340 F500 ; arch to pt 4
G1 X22.7070 Y-173.0720 F500 ; move to pt1
G0 X22.7920 Y-173.1450
G1 X18.6470 Y-173.5290 F500 ; pad 2-8, offset 0.18
G1 X14.6700 Y-173.8250 F500 ; arch to point 2
G1 X10.6880 Y-174.0510 F500 ; arch to point 2
G1 X6.5290 Y-174.2110 F500 ; arch to point 2
G1 X5.8280 Y-163.5130 F500 ; side move pt 2 to pt 3
G1 X9.9940 Y-163.3570 F500 ; arch to pt 4
G1 X13.9700 Y-163.1340 F500 ; arch to pt 4
G1 X17.9410 Y-162.8360 F500 ; arch to pt 4
G1 X22.0910 Y-162.4470 F500 ; arch to pt 4
G1 X22.7920 Y-173.1450 F500 ; move to pt1
G0 X22.8770 Y-173.2180
G1 X18.6550 Y-173.6090 F500 ; pad 2-8, offset 0.26
G1 X14.6750 Y-173.9050 F500 ; arch to point 2
G1 X10.6920 Y-174.1310 F500 ; arch to point 2
G1 X6.4540 Y-174.2940 F500 ; arch to point 2
G1 X5.7430 Y-163.4360 F500 ; side move pt 2 to pt 3
G1 X9.9900 Y-163.2770 F500 ; arch to pt 4
G1 X13.9640 Y-163.0540 F500 ; arch to pt 4
G1 X17.9330 Y-162.7570 F500 ; arch to pt 4
G1 X22.1650 Y-162.3600 F500 ; arch to pt 4
G1 X22.8770 Y-173.2180 F500 ; move to pt1
G0 X22.9620 Y-173.2900
G1 X18.6610 Y-173.6880 F500 ; pad 2-8, offset 0.34
G1 X14.6810 Y-173.9840 F500 ; arch to point 2
G1 X10.6960 Y-174.2110 F500 ; arch to point 2
G1 X6.3800 Y-174.3770 F500 ; arch to point 2
G1 X5.6570 Y-163.3590 F500 ; side move pt 2 to pt 3
G1 X9.9860 Y-163.1970 F500 ; arch to pt 4
G1 X13.9590 Y-162.9740 F500 ; arch to pt 4
G1 X17.9270 Y-162.6770 F500 ; arch to pt 4
G1 X22.2400 Y-162.2720 F500 ; arch to pt 4
G1 X22.9620 Y-173.2900 F500 ; move to pt1
G0 X23.0470 Y-173.3630
G1 X18.6670 Y-173.7680 F500 ; pad 2-8, offset 0.42
G1 X14.6860 Y-174.0640 F500 ; arch to point 2
G1 X10.7000 Y-174.2900 F500 ; arch to point 2
G1 X6.3050 Y-174.4600 F500 ; arch to point 2
G1 X5.5720 Y-163.2820 F500 ; side move pt 2 to pt 3
G1 X9.9830 Y-163.1170 F500 ; arch to pt 4
G1 X13.9540 Y-162.8940 F500 ; arch to pt 4
G1 X17.9200 Y-162.5970 F500 ; arch to pt 4
G1 X22.3140 Y-162.1850 F500 ; arch to pt 4
G1 X23.0470 Y-173.3630 F500 ; move to pt1
G0 X-6.6040 Y-174.1280
G1 X-10.6840 Y-173.9710 F500 ; pad 2-9, offset 0.1
G1 X-14.6650 Y-173.7450 F500 ; arch to point 2
G1 X-18.6410 Y-173.4490 F500 ; arch to point 2
G1 X-22.7070 Y-173.0720 F500 ; arch to point 2
G1 X-22.0170 Y-162.5340 F500 ; side move pt 2 to pt 3
G1 X-17.9470 Y-162.9160 F500 ; arch to pt 4
G1 X-13.9750 Y-163.2140 F500 ; arch to pt 4
G1 X-9.9980 Y-163.4370 F500 ; arch to pt 4
G1 X-5.9130 Y-163.5900 F500 ; arch to pt 4
G1 X-6.6040 Y-174.1280 F500 ; move to pt1
G0 X-6.5290 Y-174.2110
G1 X-10.6880 Y-174.0510 F500 ; pad 2-9, offset 0.18
G1 X-14.6700 Y-173.8250 F500 ; arch to point 2
G1 X-18.6470 Y-173.5290 F500 ; arch to point 2
G1 X-22.7920 Y-173.1450 F500 ; arch to point 2
G1 X-22.0910 Y-162.4470 F500 ; side move pt 2 to pt 3
G1 X-17.9410 Y-162.8360 F500 ; arch to pt 4
G1 X-13.9700 Y-163.1340 F500 ; arch to pt 4
G1 X-9.9940 Y-163.3570 F500 ; arch to pt 4
G1 X-5.8280 Y-163.5130 F500 ; arch to pt 4
G1 X-6.5290 Y-174.2110 F500 ; move to pt1
G0 X-6.4540 Y-174.2940
G1 X-10.6920 Y-174.1310 F500 ; pad 2-9, offset 0.26
G1 X-14.6750 Y-173.9050 F500 ; arch to point 2
G1 X-18.6550 Y-173.6090 F500 ; arch to point 2
G1 X-22.8770 Y-173.2180 F500 ; arch to point 2
G1 X-22.1650 Y-162.3600 F500 ; side move pt 2 to pt 3
G1 X-17.9330 Y-162.7570 F500 ; arch to pt 4
G1 X-13.9640 Y-163.0540 F500 ; arch to pt 4
G1 X-9.9900 Y-163.2770 F500 ; arch to pt 4
G1 X-5.7430 Y-163.4360 F500 ; arch to pt 4
G1 X-6.4540 Y-174.2940 F500 ; move to pt1
G0 X-6.3800 Y-174.3770
G1 X-10.6960 Y-174.2110 F500 ; pad 2-9, offset 0.34
G1 X-14.6810 Y-173.9840 F500 ; arch to point 2
G1 X-18.6610 Y-173.6880 F500 ; arch to point 2
G1 X-22.9620 Y-173.2900 F500 ; arch to point 2
G1 X-22.2400 Y-162.2720 F500 ; side move pt 2 to pt 3
G1 X-17.9270 Y-162.6770 F500 ; arch to pt 4
G1 X-13.9590 Y-162.9740 F500 ; arch to pt 4
G1 X-9.9860 Y-163.1970 F500 ; arch to pt 4
G1 X-5.6570 Y-163.3590 F500 ; arch to pt 4
G1 X-6.3800 Y-174.3770 F500 ; move to pt1
G0 X-6.3050 Y-174.4600
G1 X-10.7000 Y-174.2900 F500 ; pad 2-9, offset 0.42
G1 X-14.6860 Y-174.0640 F500 ; arch to point 2
G1 X-18.6670 Y-173.7680 F500 ; arch to point 2
G1 X-23.0470 Y-173.3630 F500 ; arch to point 2
G1 X-22.3140 Y-162.1850 F500 ; side move pt 2 to pt 3
G1 X-17.9200 Y-162.5970 F500 ; arch to pt 4
G1 X-13.9540 Y-162.8940 F500 ; arch to pt 4
G1 X-9.9830 Y-163.1170 F500 ; arch to pt 4
G1 X-5.5720 Y-163.2820 F500 ; arch to pt 4
G1 X-6.3050 Y-174.4600 F500 ; move to pt1
G0 X-35.8020 Y-171.3490
G1 X-39.8270 Y-170.6600 F500 ; pad 2-10, offset 0.1
G1 X-43.7440 Y-169.9170 F500 ; arch to point 2
G1 X-47.6480 Y-169.1040 F500 ; arch to point 2
G1 X-51.6300 Y-168.2000 F500 ; arch to point 2
G1 X-49.5690 Y-157.8420 F500 ; side move pt 2 to pt 3
G1 X-45.5840 Y-158.7520 F500 ; arch to pt 4
G1 X-41.6850 Y-159.5650 F500 ; arch to pt 4
G1 X-37.7710 Y-160.3060 F500 ; arch to pt 4
G1 X-33.7420 Y-160.9900 F500 ; arch to pt 4
G1 X-35.8020 Y-171.3490 F500 ; move to pt1
G0 X-35.7390 Y-171.4410
G1 X-39.8420 Y-170.7390 F500 ; pad 2-10, offset 0.18
G1 X-43.7600 Y-169.9950 F500 ; arch to point 2
G1 X-47.6640 Y-169.1830 F500 ; arch to point 2
G1 X-51.7230 Y-168.2610 F500 ; arch to point 2
G1 X-49.6320 Y-157.7460 F500 ; side move pt 2 to pt 3
G1 X-45.5680 Y-158.6740 F500 ; arch to pt 4
G1 X-41.6700 Y-159.4870 F500 ; arch to pt 4
G1 X-37.7570 Y-160.2270 F500 ; arch to pt 4
G1 X-33.6470 Y-160.9260 F500 ; arch to pt 4
G1 X-35.7390 Y-171.4410 F500 ; move to pt1
G0 X-35.6750 Y-171.5330
G1 X-39.8550 Y-170.8180 F500 ; pad 2-10, offset 0.26
G1 X-43.7750 Y-170.0740 F500 ; arch to point 2
G1 X-47.6820 Y-169.2610 F500 ; arch to point 2
G1 X-51.8170 Y-168.3220 F500 ; arch to point 2
G1 X-49.6940 Y-157.6500 F500 ; side move pt 2 to pt 3
G1 X-45.5500 Y-158.5960 F500 ; arch to pt 4
G1 X-41.6540 Y-159.4080 F500 ; arch to pt 4
G1 X-37.7430 Y-160.1490 F500 ; arch to pt 4
G1 X-33.5530 Y-160.8610 F500 ; arch to pt 4
G1 X-35.6750 Y-171.5330 F500 ; move to pt1
G0 X-35.6120 Y-171.6250
G1 X-39.8700 Y-170.8960 F500 ; pad 2-10, offset 0.34
G1 X-43.7910 Y-170.1520 F500 ; arch to point 2
G1 X-47.6980 Y-169.3390 F500 ; arch to point 2
G1 X-51.9110 Y-168.3830 F500 ; arch to point 2
G1 X-49.7570 Y-157.5530 F500 ; side move pt 2 to pt 3
G1 X-45.5340 Y-158.5170 F500 ; arch to pt 4
G1 X-41.6380 Y-159.3300 F500 ; arch to pt 4
G1 X-37.7290 Y-160.0700 F500 ; arch to pt 4
G1 X-33.4580 Y-160.7950 F500 ; arch to pt 4
G1 X-35.6120 Y-171.6250 F500 ; move to pt1
G0 X-35.5490 Y-171.7170
G1 X-39.8840 Y-170.9750 F500 ; pad 2-10, offset 0.42
G1 X-43.8070 Y-170.2300 F500 ; arch to point 2
G1 X-47.7150 Y-169.4170 F500 ; arch to point 2
G1 X-52.0050 Y-168.4440 F500 ; arch to point 2
G1 X-49.8190 Y-157.4570 F500 ; side move pt 2 to pt 3
G1 X-45.5160 Y-158.4390 F500 ; arch to pt 4
G1 X-41.6230 Y-159.2520 F500 ; arch to pt 4
G1 X-37.7150 Y-159.9910 F500 ; arch to pt 4
G1 X-33.3630 Y-160.7300 F500 ; arch to pt 4
G1 X-35.5490 Y-171.7170 F500 ; move to pt1
G0 X-64.3870 Y-164.7820
G1 X-68.2880 Y-163.5740 F500 ; pad 2-11, offset 0.1
G1 X-72.0750 Y-162.3250 F500 ; arch to point 2
G1 X-75.8390 Y-161.0110 F500 ; arch to point 2
G1 X-79.6690 Y-159.5940 F500 ; arch to point 2
G1 X-76.2740 Y-149.5940 F500 ; side move pt 2 to pt 3
G1 X-72.4420 Y-151.0160 F500 ; arch to pt 4
G1 X-68.6820 Y-152.3320 F500 ; arch to pt 4
G1 X-64.8990 Y-153.5770 F500 ; arch to pt 4
G1 X-60.9930 Y-154.7810 F500 ; arch to pt 4
G1 X-64.3870 Y-164.7820 F500 ; move to pt1
G0 X-64.3370 Y-164.8810
G1 X-68.3130 Y-163.6500 F500 ; pad 2-11, offset 0.18
G1 X-72.1000 Y-162.4010 F500 ; arch to point 2
G1 X-75.8660 Y-161.0860 F500 ; arch to point 2
G1 X-79.7700 Y-159.6430 F500 ; arch to point 2
G1 X-76.3240 Y-149.4910 F500 ; side move pt 2 to pt 3
G1 X-72.4150 Y-150.9410 F500 ; arch to pt 4
G1 X-68.6570 Y-152.2560 F500 ; arch to pt 4
G1 X-64.8740 Y-153.5010 F500 ; arch to pt 4
G1 X-60.8910 Y-154.7290 F500 ; arch to pt 4
G1 X-64.3370 Y-164.8810 F500 ; move to pt1
G0 X-64.2860 Y-164.9810
G1 X-68.3370 Y-163.7260 F500 ; pad 2-11, offset 0.26
G1 X-72.1260 Y-162.4770 F500 ; arch to point 2
G1 X-75.8930 Y-161.1610 F500 ; arch to point 2
G1 X-79.8710 Y-159.6910 F500 ; arch to point 2
G1 X-76.3730 Y-149.3870 F500 ; side move pt 2 to pt 3
G1 X-72.3880 Y-150.8660 F500 ; arch to pt 4
G1 X-68.6310 Y-152.1800 F500 ; arch to pt 4
G1 X-64.8500 Y-153.4240 F500 ; arch to pt 4
G1 X-60.7880 Y-154.6770 F500 ; arch to pt 4
G1 X-64.2860 Y-164.9810 F500 ; move to pt1
G0 X-64.2350 Y-165.0810
G1 X-68.3610 Y-163.8020 F500 ; pad 2-11, offset 0.34
G1 X-72.1520 Y-162.5530 F500 ; arch to point 2
G1 X-75.9200 Y-161.2370 F500 ; arch to point 2
G1 X-79.9710 Y-159.7390 F500 ; arch to point 2
G1 X-76.4220 Y-149.2830 F500 ; side move pt 2 to pt 3
G1 X-72.3610 Y-150.7900 F500 ; arch to pt 4
G1 X-68.6050 Y-152.1040 F500 ; arch to pt 4
G1 X-64.8250 Y-153.3480 F500 ; arch to pt 4
G1 X-60.6860 Y-154.6250 F500 ; arch to pt 4
G1 X-64.2350 Y-165.0810 F500 ; move to pt1
G0 X-64.1850 Y-165.1800
G1 X-68.3860 Y-163.8780 F500 ; pad 2-11, offset 0.42
G1 X-72.1780 Y-162.6280 F500 ; arch to point 2
G1 X-75.9470 Y-161.3120 F500 ; arch to point 2
G1 X-80.0720 Y-159.7870 F500 ; arch to point 2
G1 X-76.4710 Y-149.1790 F500 ; side move pt 2 to pt 3
G1 X-72.3330 Y-150.7150 F500 ; arch to pt 4
G1 X-68.5790 Y-152.0280 F500 ; arch to pt 4
G1 X-64.8020 Y-153.2720 F500 ; arch to pt 4
G1 X-60.5840 Y-154.5730 F500 ; arch to pt 4
G1 X-64.1850 Y-165.1800 F500 ; move to pt1
G0 X-91.8710 Y-154.5400
G1 X-95.5810 Y-152.8330 F500 ; pad 2-12, offset 0.1
G1 X-99.1720 Y-151.1010 F500 ; arch to point 2
G1 X-102.7330 Y-149.3060 F500 ; arch to point 2
G1 X-106.3450 Y-147.4020 F500 ; arch to point 2
G1 X-101.6740 Y-137.9310 F500 ; side move pt 2 to pt 3
G1 X-98.0600 Y-139.8410 F500 ; arch to pt 4
G1 X-94.5040 Y-141.6360 F500 ; arch to pt 4
G1 X-90.9160 Y-143.3640 F500 ; arch to pt 4
G1 X-87.2000 Y-145.0680 F500 ; arch to pt 4
G1 X-91.8710 Y-154.5400 F500 ; move to pt1
G0 X-91.8340 Y-154.6450
G1 X-95.6150 Y-152.9050 F500 ; pad 2-12, offset 0.18
G1 X-99.2080 Y-151.1730 F500 ; arch to point 2
G1 X-102.7690 Y-149.3780 F500 ; arch to point 2
G1 X-106.4510 Y-147.4370 F500 ; arch to point 2
G1 X-101.7090 Y-137.8220 F500 ; side move pt 2 to pt 3
G1 X-98.0240 Y-139.7700 F500 ; arch to pt 4
G1 X-94.4690 Y-141.5640 F500 ; arch to pt 4
G1 X-90.8810 Y-143.2920 F500 ; arch to pt 4
G1 X-87.0920 Y-145.0300 F500 ; arch to pt 4
G1 X-91.8340 Y-154.6450 F500 ; move to pt1
G0 X-91.7970 Y-154.7510
G1 X-95.6490 Y-152.9780 F500 ; pad 2-12, offset 0.26
G1 X-99.2430 Y-151.2450 F500 ; arch to point 2
G1 X-102.8060 Y-149.4490 F500 ; arch to point 2
G1 X-106.5570 Y-147.4720 F500 ; arch to point 2
G1 X-101.7450 Y-137.7130 F500 ; side move pt 2 to pt 3
G1 X-97.9870 Y-139.6990 F500 ; arch to pt 4
G1 X-94.4340 Y-141.4920 F500 ; arch to pt 4
G1 X-90.8480 Y-143.2190 F500 ; arch to pt 4
G1 X-86.9840 Y-144.9920 F500 ; arch to pt 4
G1 X-91.7970 Y-154.7510 F500 ; move to pt1
G0 X-91.7590 Y-154.8560
G1 X-95.6830 Y-153.0500 F500 ; pad 2-12, offset 0.34
G1 X-99.2780 Y-151.3170 F500 ; arch to point 2
G1 X-102.8420 Y-149.5200 F500 ; arch to point 2
G1 X-106.6640 Y-147.5060 F500 ; arch to point 2
G1 X-101.7800 Y-137.6030 F500 ; side move pt 2 to pt 3
G1 X-97.9500 Y-139.6270 F500 ; arch to pt 4
G1 X-94.3980 Y-141.4200 F500 ; arch to pt 4
G1 X-90.8130 Y-143.1470 F500 ; arch to pt 4
G1 X-86.8760 Y-144.9530 F500 ; arch to pt 4
G1 X-91.7590 Y-154.8560 F500 ; move to pt1
G0 X-91.7220 Y-154.9610
G1 X-95.7180 Y-153.1230 F500 ; pad 2-12, offset 0.42
G1 X-99.3140 Y-151.3880 F500 ; arch to point 2
G1 X-102.8790 Y-149.5910 F500 ; arch to point 2
G1 X-106.7700 Y-147.5410 F500 ; arch to point 2
G1 X-101.8150 Y-137.4940 F500 ; side move pt 2 to pt 3
G1 X-97.9130 Y-139.5570 F500 ; arch to pt 4
G1 X-94.3630 Y-141.3490 F500 ; arch to pt 4
G1 X-90.7800 Y-143.0740 F500 ; arch to pt 4
G1 X-86.7680 Y-144.9150 F500 ; arch to pt 4
G1 X-91.7220 Y-154.9610 F500 ; move to pt1
G0 X-117.7830 Y-140.7990
G1 X-121.2380 Y-138.6220 F500 ; pad 2-13, offset 0.1
G1 X-124.5730 Y-136.4360 F500 ; arch to point 2
G1 X-127.8680 Y-134.1920 F500 ; arch to point 2
G1 X-131.2010 Y-131.8330 F500 ; arch to point 2
G1 X-125.3340 Y-123.0520 F500 ; side move pt 2 to pt 3
G1 X-122.0000 Y-125.4170 F500 ; arch to pt 4
G1 X-118.7090 Y-127.6610 F500 ; arch to pt 4
G1 X-115.3770 Y-129.8430 F500 ; arch to pt 4
G1 X-111.9160 Y-132.0170 F500 ; arch to pt 4
G1 X-117.7830 Y-140.7990 F500 ; move to pt1
G0 X-117.7600 Y-140.9080
G1 X-121.2820 Y-138.6890 F500 ; pad 2-13, offset 0.18
G1 X-124.6170 Y-136.5030 F500 ; arch to point 2
G1 X-127.9140 Y-134.2580 F500 ; arch to point 2
G1 X-131.3110 Y-131.8530 F500 ; arch to point 2
G1 X-125.3550 Y-122.9390 F500 ; side move pt 2 to pt 3
G1 X-121.9550 Y-125.3510 F500 ; arch to pt 4
G1 X-118.6650 Y-127.5940 F500 ; arch to pt 4
G1 X-115.3330 Y-129.7760 F500 ; arch to pt 4
G1 X-111.8040 Y-131.9940 F500 ; arch to pt 4
G1 X-117.7600 Y-140.9080 F500 ; move to pt1
G0 X-117.7370 Y-141.0170
G1 X-121.3250 Y-138.7570 F500 ; pad 2-13, offset 0.26
G1 X-124.6620 Y-136.5690 F500 ; arch to point 2
G1 X-127.9600 Y-134.3230 F500 ; arch to point 2
G1 X-131.4210 Y-131.8740 F500 ; arch to point 2
G1 X-125.3760 Y-122.8260 F500 ; side move pt 2 to pt 3
G1 X-121.9090 Y-125.2860 F500 ; arch to pt 4
G1 X-118.6200 Y-127.5280 F500 ; arch to pt 4
G1 X-115.2910 Y-129.7080 F500 ; arch to pt 4
G1 X-111.6920 Y-131.9700 F500 ; arch to pt 4
G1 X-117.7370 Y-141.0170 F500 ; move to pt1
G0 X-117.7140 Y-141.1270
G1 X-121.3680 Y-138.8240 F500 ; pad 2-13, offset 0.34
G1 X-124.7060 Y-136.6360 F500 ; arch to point 2
G1 X-128.0050 Y-134.3890 F500 ; arch to point 2
G1 X-131.5310 Y-131.8940 F500 ; arch to point 2
G1 X-125.3960 Y-122.7130 F500 ; side move pt 2 to pt 3
G1 X-121.8640 Y-125.2200 F500 ; arch to pt 4
G1 X-118.5760 Y-127.4610 F500 ; arch to pt 4
G1 X-115.2470 Y-129.6410 F500 ; arch to pt 4
G1 X-111.5790 Y-131.9450 F500 ; arch to pt 4
G1 X-117.7140 Y-141.1270 F500 ; move to pt1
G0 X-117.6900 Y-141.2360
G1 X-121.4120 Y-138.8910 F500 ; pad 2-13, offset 0.42
G1 X-124.7510 Y-136.7020 F500 ; arch to point 2
G1 X-128.0500 Y-134.4550 F500 ; arch to point 2
G1 X-131.6410 Y-131.9140 F500 ; arch to point 2
G1 X-125.4170 Y-122.6000 F500 ; side move pt 2 to pt 3
G1 X-121.8180 Y-125.1550 F500 ; arch to pt 4
G1 X-118.5310 Y-127.3950 F500 ; arch to pt 4
G1 X-115.2040 Y-129.5740 F500 ; arch to pt 4
G1 X-111.4670 Y-131.9220 F500 ; arch to pt 4
G1 X-117.6900 Y-141.2360 F500 ; move to pt1
G0 X-141.6800 Y-123.7930
G1 X-144.8210 Y-121.1840 F500 ; pad 2-14, offset 0.1
G1 X-147.8420 Y-118.5810 F500 ; arch to point 2
G1 X-150.8160 Y-115.9260 F500 ; arch to point 2
G1 X-153.8130 Y-113.1520 F500 ; arch to point 2
G1 X-146.8490 Y-105.2120 F500 ; side move pt 2 to pt 3
G1 X-143.8530 Y-107.9920 F500 ; arch to pt 4
G1 X-140.8830 Y-110.6460 F500 ; arch to pt 4
G1 X-137.8640 Y-113.2450 F500 ; arch to pt 4
G1 X-134.7160 Y-115.8520 F500 ; arch to pt 4
G1 X-141.6800 Y-123.7930 F500 ; move to pt1
G0 X-141.6710 Y-123.9040
G1 X-144.8730 Y-121.2450 F500 ; pad 2-14, offset 0.18
G1 X-147.8950 Y-118.6410 F500 ; arch to point 2
G1 X-150.8700 Y-115.9860 F500 ; arch to point 2
G1 X-153.9240 Y-113.1580 F500 ; arch to point 2
G1 X-146.8560 Y-105.0970 F500 ; side move pt 2 to pt 3
G1 X-143.8000 Y-107.9330 F500 ; arch to pt 4
G1 X-140.8300 Y-110.5860 F500 ; arch to pt 4
G1 X-137.8120 Y-113.1840 F500 ; arch to pt 4
G1 X-134.6020 Y-115.8430 F500 ; arch to pt 4
G1 X-141.6710 Y-123.9040 F500 ; move to pt1
G0 X-141.6620 Y-124.0150
G1 X-144.9240 Y-121.3060 F500 ; pad 2-14, offset 0.26
G1 X-147.9470 Y-118.7020 F500 ; arch to point 2
G1 X-150.9240 Y-116.0440 F500 ; arch to point 2
G1 X-154.0360 Y-113.1640 F500 ; arch to point 2
G1 X-146.8620 Y-104.9830 F500 ; side move pt 2 to pt 3
G1 X-143.7460 Y-107.8740 F500 ; arch to pt 4
G1 X-140.7780 Y-110.5260 F500 ; arch to pt 4
G1 X-137.7610 Y-113.1220 F500 ; arch to pt 4
G1 X-134.4880 Y-115.8350 F500 ; arch to pt 4
G1 X-141.6620 Y-124.0150 F500 ; move to pt1
G0 X-141.6530 Y-124.1270
G1 X-144.9760 Y-121.3670 F500 ; pad 2-14, offset 0.34
G1 X-148.0000 Y-118.7620 F500 ; arch to point 2
G1 X-150.9780 Y-116.1040 F500 ; arch to point 2
G1 X-154.1480 Y-113.1700 F500 ; arch to point 2
G1 X-146.8670 Y-104.8680 F500 ; side move pt 2 to pt 3
G1 X-143.6920 Y-107.8150 F500 ; arch to pt 4
G1 X-140.7250 Y-110.4660 F500 ; arch to pt 4
G1 X-137.7090 Y-113.0620 F500 ; arch to pt 4
G1 X-134.3730 Y-115.8250 F500 ; arch to pt 4
G1 X-141.6530 Y-124.1270 F500 ; move to pt1
G0 X-141.6450 Y-124.2380
G1 X-145.0280 Y-121.4280 F500 ; pad 2-14, offset 0.42
G1 X-148.0530 Y-118.8220 F500 ; arch to point 2
G1 X-151.0310 Y-116.1630 F500 ; arch to point 2
G1 X-154.2590 Y-113.1760 F500 ; arch to point 2
G1 X-146.8730 Y-104.7530 F500 ; side move pt 2 to pt 3
G1 X-143.6380 Y-107.7560 F500 ; arch to pt 4
G1 X-140.6720 Y-110.4060 F500 ; arch to pt 4
G1 X-137.6580 Y-113.0000 F500 ; arch to pt 4
G1 X-134.2590 Y-115.8160 F500 ; arch to pt 4
G1 X-141.6450 Y-124.2380 F500 ; move to pt1
G0 X-163.1520 Y-103.8130
G1 X-165.9260 Y-100.8160 F500 ; pad 2-15, offset 0.1
G1 X-168.5810 Y-97.8420 F500 ; arch to point 2
G1 X-171.1840 Y-94.8210 F500 ; arch to point 2
G1 X-173.7930 Y-91.6800 F500 ; arch to point 2
G1 X-165.8520 Y-84.7160 F500 ; side move pt 2 to pt 3
G1 X-163.2450 Y-87.8640 F500 ; arch to pt 4
G1 X-160.6460 Y-90.8830 F500 ; arch to pt 4
G1 X-157.9920 Y-93.8530 F500 ; arch to pt 4
G1 X-155.2120 Y-96.8490 F500 ; arch to pt 4
G1 X-163.1520 Y-103.8130 F500 ; move to pt1
G0 X-163.1580 Y-103.9240
G1 X-165.9860 Y-100.8700 F500 ; pad 2-15, offset 0.18
G1 X-168.6410 Y-97.8950 F500 ; arch to point 2
G1 X-171.2450 Y-94.8730 F500 ; arch to point 2
G1 X-173.9040 Y-91.6710 F500 ; arch to point 2
G1 X-165.8430 Y-84.6020 F500 ; side move pt 2 to pt 3
G1 X-163.1840 Y-87.8120 F500 ; arch to pt 4
G1 X-160.5860 Y-90.8300 F500 ; arch to pt 4
G1 X-157.9330 Y-93.8000 F500 ; arch to pt 4
G1 X-155.0970 Y-96.8560 F500 ; arch to pt 4
G1 X-163.1580 Y-103.9240 F500 ; move to pt1
G0 X-163.1640 Y-104.0360
G1 X-166.0440 Y-100.9240 F500 ; pad 2-15, offset 0.26
G1 X-168.7020 Y-97.9470 F500 ; arch to point 2
G1 X-171.3060 Y-94.9240 F500 ; arch to point 2
G1 X-174.0150 Y-91.6620 F500 ; arch to point 2
G1 X-165.8350 Y-84.4880 F500 ; side move pt 2 to pt 3
G1 X-163.1220 Y-87.7610 F500 ; arch to pt 4
G1 X-160.5260 Y-90.7780 F500 ; arch to pt 4
G1 X-157.8740 Y-93.7460 F500 ; arch to pt 4
G1 X-154.9830 Y-96.8620 F500 ; arch to pt 4
G1 X-163.1640 Y-104.0360 F500 ; move to pt1
G0 X-163.1700 Y-104.1480
G1 X-166.1040 Y-100.9780 F500 ; pad 2-15, offset 0.34
G1 X-168.7620 Y-98.0000 F500 ; arch to point 2
G1 X-171.3670 Y-94.9760 F500 ; arch to point 2
G1 X-174.1270 Y-91.6530 F500 ; arch to point 2
G1 X-165.8250 Y-84.3730 F500 ; side move pt 2 to pt 3
G1 X-163.0620 Y-87.7090 F500 ; arch to pt 4
G1 X-160.4660 Y-90.7250 F500 ; arch to pt 4
G1 X-157.8150 Y-93.6920 F500 ; arch to pt 4
G1 X-154.8680 Y-96.8670 F500 ; arch to pt 4
G1 X-163.1700 Y-104.1480 F500 ; move to pt1
G0 X-163.1760 Y-104.2590
G1 X-166.1630 Y-101.0310 F500 ; pad 2-15, offset 0.42
G1 X-168.8220 Y-98.0530 F500 ; arch to point 2
G1 X-171.4280 Y-95.0280 F500 ; arch to point 2
G1 X-174.2380 Y-91.6450 F500 ; arch to point 2
G1 X-165.8160 Y-84.2590 F500 ; side move pt 2 to pt 3
G1 X-163.0000 Y-87.6580 F500 ; arch to pt 4
G1 X-160.4060 Y-90.6720 F500 ; arch to pt 4
G1 X-157.7560 Y-93.6380 F500 ; arch to pt 4
G1 X-154.7530 Y-96.8730 F500 ; arch to pt 4
G1 X-163.1760 Y-104.2590 F500 ; move to pt1
G0 X-179.5150 Y-84.3550
G1 X-181.9320 Y-81.0630 F500 ; pad 2-16, offset 0.1
G1 X-184.2340 Y-77.8080 F500 ; arch to point 2
G1 X-186.4780 Y-74.5120 F500 ; arch to point 2
G1 X-188.7140 Y-71.0950 F500 ; arch to point 2
G1 X-180.0370 Y-65.0750 F500 ; side move pt 2 to pt 3
G1 X-177.8020 Y-68.4980 F500 ; arch to pt 4
G1 X-175.5620 Y-71.7920 F500 ; arch to pt 4
G1 X-173.2610 Y-75.0430 F500 ; arch to pt 4
G1 X-170.8380 Y-78.3350 F500 ; arch to pt 4
G1 X-179.5150 Y-84.3550 F500 ; move to pt1
G0 X-179.5340 Y-84.4650
G1 X-181.9980 Y-81.1100 F500 ; pad 2-16, offset 0.18
G1 X-184.3000 Y-77.8530 F500 ; arch to point 2
G1 X-186.5440 Y-74.5560 F500 ; arch to point 2
G1 X-188.8240 Y-71.0740 F500 ; arch to point 2
G1 X-180.0150 Y-64.9630 F500 ; side move pt 2 to pt 3
G1 X-177.7360 Y-68.4530 F500 ; arch to pt 4
G1 X-175.4960 Y-71.7460 F500 ; arch to pt 4
G1 X-173.1960 Y-74.9970 F500 ; arch to pt 4
G1 X-170.7250 Y-78.3540 F500 ; arch to pt 4
G1 X-179.5340 Y-84.4650 F500 ; move to pt1
G0 X-179.5520 Y-84.5750
G1 X-182.0620 Y-81.1570 F500 ; pad 2-16, offset 0.26
G1 X-184.3650 Y-77.8990 F500 ; arch to point 2
G1 X-186.6110 Y-74.6000 F500 ; arch to point 2
G1 X-188.9330 Y-71.0520 F500 ; arch to point 2
G1 X-179.9930 Y-64.8500 F500 ; side move pt 2 to pt 3
G1 X-177.6690 Y-68.4090 F500 ; arch to pt 4
G1 X-175.4310 Y-71.7010 F500 ; arch to pt 4
G1 X-173.1320 Y-74.9500 F500 ; arch to pt 4
G1 X-170.6120 Y-78.3730 F500 ; arch to pt 4
G1 X-179.5520 Y-84.5750 F500 ; move to pt1
G0 X-179.5710 Y-84.6850
G1 X-182.1270 Y-81.2040 F500 ; pad 2-16, offset 0.34
G1 X-184.4310 Y-77.9440 F500 ; arch to point 2
G1 X-186.6770 Y-74.6450 F500 ; arch to point 2
G1 X-189.0430 Y-71.0310 F500 ; arch to point 2
G1 X-179.9700 Y-64.7370 F500 ; side move pt 2 to pt 3
G1 X-177.6030 Y-68.3650 F500 ; arch to pt 4
G1 X-175.3650 Y-71.6550 F500 ; arch to pt 4
G1 X-173.0670 Y-74.9030 F500 ; arch to pt 4
G1 X-170.4980 Y-78.3910 F500 ; arch to pt 4
G1 X-179.5710 Y-84.6850 F500 ; move to pt1
G0 X-179.5890 Y-84.7960
G1 X-182.1930 Y-81.2500 F500 ; pad 2-16, offset 0.42
G1 X-184.4970 Y-77.9900 F500 ; arch to point 2
G1 X-186.7430 Y-74.6900 F500 ; arch to point 2
G1 X-189.1530 Y-71.0100 F500 ; arch to point 2
G1 X-179.9490 Y-64.6250 F500 ; side move pt 2 to pt 3
G1 X-177.5360 Y-68.3210 F500 ; arch to pt 4
G1 X-175.2990 Y-71.6090 F500 ; arch to pt 4
G1 X-173.0020 Y-74.8560 F500 ; arch to pt 4
G1 X-170.3850 Y-78.4100 F500 ; arch to pt 4
G1 X-179.5890 Y-84.7960 F500 ; move to pt1
M5
G0 X0 Y0 Z0