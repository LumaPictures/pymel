//Maya ASCII 2008 scene
//Name: skel2.ma
//Last modified: Thu, Mar 06, 2008 03:03:14 AM
//Codeset: UTF-8
requires maya "2008";
currentUnit -l centimeter -a degree -t pal;
fileInfo "application" "maya";
fileInfo "product" "Maya Unlimited 2008";
fileInfo "version" "2008 x64";
fileInfo "cutIdentifier" "200708030010-704171";
fileInfo "osv" "Linux 2.6.23.1-mactel #1 SMP PREEMPT Sun Nov 25 05:39:00 CET 2007 x86_64";
createNode transform -s -n "persp";
	setAttr ".t" -type "double3" -9.1916636240857361 17.288683234717222 44.547012859133076 ;
	setAttr ".r" -type "double3" -9.3383527296038871 -7.7999999999990965 1.0032051520641137e-16 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v";
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 47.143556815954355;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" -0.0013327598571777344 9.1253437511622906 0.037933647632598877 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	setAttr ".t" -type "double3" 0 100 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".coi" 100;
	setAttr ".ow" 20.486656200941916;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".t" -type "double3" -0.23747501657346648 11.042588270666316 100 ;
createNode camera -s -n "frontShape" -p "front";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".coi" 100;
	setAttr ".ow" 37.817896389324972;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".t" -type "double3" 100 9.0252237230870609 -0.43081369945151671 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".coi" 100;
	setAttr ".ow" 40.59270621093841;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode joint -n "FBX_Hips";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0 11.290417510307522 -0.30575371918217331 ;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 15.65100263999998 0 0 ;
	setAttr ".bps" -type "matrix" 1 0 0 0 0 0.96292280248626105 0.26977708659559096 0
		 0 -0.26977708659559096 0.96292280248626105 0 0 11.290417510307522 -0.30575371918217331 1
		;
	setAttr -l on ".amt" 1275076992;
	setAttr ".aim" -type "double3" 0 1 6.0589463165214583e-16 ;
	setAttr ".up" -type "double3" 1 0 0 ;
	setAttr ".dim" -type "double3" 8.911 8.911 8.911 ;
createNode joint -n "FBX_Spine" -p "FBX_Hips";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0 0.73294791973833107 -2.7755575615628914e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -8.0733709891413508e-16 9.9726475229999956 89.999999999999986 ;
	setAttr ".bps" -type "matrix" 2.2204460492503131e-16 0.99509301942264905 0.098943836070343738 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.3877787807814454e-17 -0.098943836070343738 0.99509301942264905 0
		 0 11.996189775258431 -0.10802116476886733 1;
	setAttr -l on ".amt" 1275085184;
	setAttr ".aim" -type "double3" 0.99999999999999989 -3.6841970500479278e-31 1.3826790384796108e-16 ;
	setAttr ".up" -type "double3" -3.6841970500479282e-31 -0.99999999999999989 -5.0940620347296877e-47 ;
	setAttr ".dim" -type "double3" 10.861175 10.861175 10.861175 ;
createNode joint -n "FBX_Spine1" -p "FBX_Spine";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.6059012883365249 -3.3833774298022766e-31 1.6653345369377348e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 13.056123070000011 0 ;
	setAttr ".bps" -type "matrix" 2.1316951863865569e-16 0.99172106330715759 -0.128410796247513 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.3680105952454152e-17 0.128410796247513 0.99172106330715759 0
		 3.565817171172828e-16 13.594210937163945 0.05087286904945576 1;
	setAttr -l on ".amt" 1275093376;
	setAttr ".aim" -type "double3" 1 4.841360598000727e-31 1.3627218615701425e-16 ;
	setAttr ".up" -type "double3" 4.841360598000727e-31 -1 6.59742792663989e-47 ;
	setAttr ".dim" -type "double3" 10.915259 10.915259 10.915259 ;
createNode joint -n "FBX_Spine2" -p "FBX_Spine1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.6294198485169147 4.221638438096821e-31 -1.1102230246251565e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 1.5859255500000571 0 ;
	setAttr ".bps" -type "matrix" 2.113254464861858e-16 0.98778726979368714 -0.15580856726615877 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.9555411278822762e-17 0.15580856726615877 0.98778726979368714 0
		 7.0392436188590434e-16 15.210140921908927 -0.15836223112010339 1;
	setAttr -l on ".amt" 1275101568;
	setAttr ".aim" -type "double3" 1 1.6192848600404366e-31 6.3039807580592448e-32 ;
	setAttr ".up" -type "double3" 1.6192848600404366e-31 -1 1.020794059951157e-62 ;
	setAttr ".dim" -type "double3" 10.915259 10.915259 10.915259 ;
createNode joint -n "FBX_Spine3" -p "FBX_Spine2";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.2179155821930434 -2.0337820212729211e-31 2.7755575615628914e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 -11.565578400000154 0 ;
	setAttr ".bps" -type "matrix" 2.209797897348894e-16 0.99896907691404224 0.045395851897569228 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.5774640627485565e-17 -0.045395851897569228 0.99896907691404224 0
		 9.6130091607533248e-16 16.413182429682582 -0.34812391303273083 1;
	setAttr -l on ".amt" 1275126144;
	setAttr ".aim" -type "double3" 1 -1.4022073573114307e-30 -9.8671570810686317e-17 ;
	setAttr ".up" -type "double3" -1.4022073573114307e-30 -1 1.3835800254822019e-46 ;
	setAttr ".dim" -type "double3" 14.690325 14.690325 14.690325 ;
createNode joint -n "FBX_Neck" -p "FBX_Spine3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.1251701128334721 -1.5264800368591707e-30 -8.3266726846886741e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 -4.0455647780000676 0 ;
	setAttr ".bps" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr -l on ".amt" 1275109760;
	setAttr ".aim" -type "double3" 1 8.6764036996141361e-31 3.2678986476336168e-32 ;
	setAttr ".up" -type "double3" 8.6764036996141361e-31 -1 2.8353607916292344e-62 ;
	setAttr ".dim" -type "double3" 10.432663 10.432663 10.432663 ;
createNode joint -n "FBX_Neck1" -p "FBX_Neck";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.90920262879895186 1.5490976766435683e-30 -3.8857805861880479e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 7.557959081000055 0 ;
	setAttr ".bps" -type "matrix" 2.1898562510217626e-16 0.99987373456677664 -0.01589071815515776 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 3.9264431351556042e-17 0.01589071815515776 0.99987373456677664 0
		 1.4120088374132143e-15 18.440282855871136 -0.19179676487531067 1;
	setAttr -l on ".amt" 1275117952;
	setAttr ".aim" -type "double3" 1 1.8052794632966261e-31 -2.0325639795505728e-16 ;
	setAttr ".up" -type "double3" 1.8052794632966258e-31 -1 -3.6693460101191121e-47 ;
createNode joint -n "FBX_Head" -p "FBX_Neck1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.0924359929576617 4.1099345013223613e-31 -2.2204460492503131e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 -3.921680335000004 0 ;
	setAttr ".bps" -type "matrix" 2.2115826839442644e-16 0.99861931185935604 0.052530657539630252 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr -l on ".amt" 1278345600;
	setAttr ".aim" -type "double3" 1 1.8561353654274435e-30 -1.7415188625183815e-16 ;
	setAttr ".up" -type "double3" 1.8561353654274439e-30 -1 -3.2324947502793426e-46 ;
	setAttr ".dim" -type "double3" 19.137126 19.137126 19.137126 ;
createNode joint -n "FBX_LeftEye" -p "FBX_Head";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.35145840449401444 -0.29225669056177106 0.60898929957919268 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 0 -89.999999999999986 ;
	setAttr ".bps" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 0.29225669056177278 19.851563453626383 0.41745445901943362 1;
	setAttr -l on ".amt" 1278509442;
	setAttr ".aim" -type "double3" 0 0 1 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightEye" -p "FBX_Head";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.35145840449401433 0.29144088923931144 0.60898929957919268 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 0 -89.999999999999986 ;
	setAttr ".bps" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 -0.29144088923930972 19.851563453626383 0.41745445901943362 1;
	setAttr -l on ".amt" 1278509441;
	setAttr ".aim" -type "double3" 0 0 1 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube16" -p "FBX_Neck1";
createNode mesh -n "pCubeShape1" -p "pCube16";
	setAttr -k off ".v";
	setAttr -s 16 ".iog";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode joint -n "FBX_NeckRoll" -p "FBX_Neck";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr -l on ".amt" 1279033728;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 15 15 15 ;
createNode joint -n "FBX_LeftShoulder" -p "FBX_Spine3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.1036875395607693 -0.59846639999999973 0.32383580444340093 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 14.362033110720015 20.641262271775073 -80.8437137376566 ;
	setAttr ".bps" -type "matrix" 0.83161908486574476 -0.34209624156754381 -0.43746983803734568 0
		 0.40812744501784315 0.91070112398666447 0.063682426089405872 0 0.37661875459178623 -0.23150296817705379 0.89697530033716399 0
		 0.59846640000000095 17.501031350061492 0.025480877690902903 1;
	setAttr -l on ".amt" 1275912578;
	setAttr ".aim" -type "double3" 1 2.7630338920682942e-15 -2.3515182060155698e-16 ;
	setAttr ".up" -type "double3" -2.7630338920682946e-15 1 6.497324501036653e-31 ;
	setAttr ".dim" -type "double3" 8.451846 8.451846 8.451846 ;
createNode joint -n "FBX_LeftArm" -p "FBX_LeftShoulder";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.4163909364405824 4.3298697960381105e-15 -5.5511151231257857e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.17514848874978464 -22.090761573863812 -4.1975289187577474 ;
	setAttr ".bps" -type "matrix" 0.64363943585712535 -0.76264928926282138 0.063987015842547734 0
		 0.76398091207252428 0.64521625466751731 0.0053991389734481254 0 -0.045403112210011143 0.045409759961204263 0.99793612576252122 0
		 1.7763641343748549 17.016489334114837 -0.59414743587132335 1;
	setAttr -l on ".amt" 1276051842;
	setAttr ".aim" -type "double3" 1 -3.7675624877711346e-15 4.2268916455912184e-16 ;
	setAttr ".up" -type "double3" -3.7675624877711338e-15 -1 -1.5925078403802673e-30 ;
	setAttr ".dim" -type "double3" 26.125045 26.125045 26.125045 ;
createNode joint -n "FBX_LeftForeArm" -p "FBX_LeftArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 2.763029379803347 -2.9901889802249744e-15 6.1977251948291957e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.16126764774810848 0.0069461608715560312 0.032664452757393499 ;
	setAttr ".bps" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 3.5547588056481416 14.909266941395517 -0.41734943117242168 1;
	setAttr -l on ".amt" 1276100994;
	setAttr ".aim" -type "double3" 1 7.5302379564533986e-16 4.2283112568140573e-16 ;
	setAttr ".up" -type "double3" 7.5302379564533976e-16 -1 3.1840189917760384e-31 ;
	setAttr ".dim" -type "double3" 24.72653 24.72653 24.72653 ;
createNode joint -n "FBX_LeftHand" -p "FBX_LeftForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 3.3846771932282129 3.288565543181897e-15 -1.4283160789765633e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 0 -9.083 ;
	setAttr ".pa" -type "double3" -18.004252702619095 -17.850845357872299 42.825197541748722 ;
	setAttr ".bps" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 5.5097646627003369 12.148202402262493 -0.31480962430229931 1;
	setAttr -l on ".amt" 1276215682;
	setAttr ".aim" -type "double3" 1 4.4753072109528705e-14 -1.3166875086201895e-14 ;
	setAttr ".up" -type "double3" 4.4753072109528699e-14 -1 -5.8925811018995025e-28 ;
	setAttr ".dim" -type "double3" 2.596201 2.596201 2.596201 ;
createNode joint -n "FBX_LeftHandThumb1" -p "FBX_LeftHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.076525269383702535 0.023547569757453157 0.19836057277298721 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 5;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -36.16227161689136 -15.726468874803764 -18.234835146250195 ;
	setAttr ".bps" -type "matrix" 0.27578017479248546 -0.91444587836227009 0.29619930914450476 0
		 0.83216325399207891 0.07290562571281739 -0.54971728046763901 0 0.48109210541926434 0.39808730862171193 0.78107418394002814 0
		 5.4800090076208514 12.228226722954085 -0.11867642768531272 1;
	setAttr -l on ".amt" 1276805506;
	setAttr ".aim" -type "double3" 1 4.5526064405119308e-15 1.2804205613939806e-15 ;
	setAttr ".up" -type "double3" -4.5526064405119308e-15 1 -5.8292508943661383e-30 ;
	setAttr ".dim" -type "double3" 4.827585 4.827585 4.827585 ;
createNode joint -n "FBX_LeftHandThumb2" -p "FBX_LeftHandThumb1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.78036916329648875 1.0269562977782698e-15 -1.3877787807814457e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 1;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 86.433335058096915 -1.6818117033661009 5.2681824858469266 ;
	setAttr ".bps" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.6952193518774239 11.514621357976598 0.1124683793607818 1;
	setAttr -l on ".amt" 1276813698;
	setAttr ".aim" -type "double3" 1 -3.1499922494309309e-16 8.8199782984066064e-15 ;
	setAttr ".up" -type "double3" 3.1499922494309309e-16 1 2.7782863280129819e-30 ;
	setAttr ".dim" -type "double3" 3.333332 3.333332 3.333332 ;
createNode joint -n "FBX_LeftHandThumb3" -p "FBX_LeftHandThumb2";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.35245262105826525 4.4408920985006153e-16 2.2204460492503348e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 1;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.8238613234834604 11.200298372243006 0.20667641443037332 1;
	setAttr -l on ".amt" 1276821890;
	setAttr ".aim" -type "double3" 1 -5.7326880180942817e-16 -4.5861504144754254e-15 ;
	setAttr ".up" -type "double3" 5.7326880180942817e-16 1 -2.6290969530241395e-30 ;
	setAttr ".dim" -type "double3" 3.333332 3.333332 3.333332 ;
createNode joint -n "FBX_LeftHandThumb4" -p "FBX_LeftHandThumb3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.38733069761372629 -8.8817841970012326e-16 -3.944304526105059e-30 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.9652334728945267 10.854870549988012 0.31020710696646492 1;
	setAttr -l on ".amt" 1276830082;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftHandMiddle0" -p "FBX_LeftHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.10915409999999959 -7.0518867354993834e-16 -4.5520648033906218e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.97155148369782274 5.8958241999368628 8.6991533247717445 ;
	setAttr ".bps" -type "matrix" 0.69316755490681126 -0.71720363427704981 -0.071677666007649674 0
		 0.7199158164255508 0.69376628281126029 0.020237640538819459 0 0.035213038563080321 -0.06562996125275157 0.99722251784700344 0
		 5.5728125968573092 12.059159489864832 -0.31150276822885303 1;
	setAttr -l on ".amt" 1276969346;
	setAttr ".aim" -type "double3" 0.99999999999999989 -4.2568667019439236e-15 1.6372564238245859e-16 ;
	setAttr ".up" -type "double3" 1.6372564238245859e-16 -6.9695823531226681e-31 -0.99999999999999989 ;
	setAttr ".dim" -type "double3" 6.340006 6.340006 6.340006 ;
createNode joint -n "FBX_LeftHandMiddle1" -p "FBX_LeftHandMiddle0";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.67809966018133316 4.0050428251614534e-16 1.5265566588595902e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.13342505952997472 -7.8431989478890607 -12.544067895645147 ;
	setAttr ".bps" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.042849280288344 11.572823949180748 -0.36010736919123121 1;
	setAttr -l on ".amt" 1276977538;
	setAttr ".aim" -type "double3" 1 -1.2520547009479385e-15 -6.2602735047396925e-16 ;
	setAttr ".up" -type "double3" -6.2602735047396925e-16 7.8382048708291583e-31 -1 ;
	setAttr ".dim" -type "double3" 5.693803 5.693803 5.693803 ;
createNode joint -n "FBX_LeftHandMiddle2" -p "FBX_LeftHandMiddle1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.35468834509693448 -1.5543122344752148e-15 6.8782774695160208e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.2273583750410744 11.270714534454719 -0.3379687686251196 1;
	setAttr -l on ".amt" 1276985730;
	setAttr ".aim" -type "double3" 0.99999999999999989 1.3110122964947695e-14 -1.0084709973036689e-15 ;
	setAttr ".up" -type "double3" -1.0084709973036691e-15 -1.3221178781234537e-29 -1 ;
	setAttr ".dim" -type "double3" 3.589571 3.589571 3.589571 ;
createNode joint -n "FBX_LeftHandMiddle3" -p "FBX_LeftHandMiddle2";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.44035893053684116 2.2204460492503151e-15 -4.1693089501269e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.4564333609062823 10.895634324989402 -0.31048286274848064 1;
	setAttr -l on ".amt" 1276993922;
	setAttr ".aim" -type "double3" 1 -2.8200216486075699e-15 0 ;
	setAttr ".up" -type "double3" 0 0 -1 ;
	setAttr ".dim" -type "double3" 3.094458 3.094458 3.094458 ;
createNode joint -n "FBX_LeftHandMiddle4" -p "FBX_LeftHandMiddle3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.62990893714498686 -1.3322676295501873e-15 -9.6748875453842723e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.7841123765150781 10.359102964536724 -0.27116580442037141 1;
	setAttr -l on ".amt" 1277002114;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 0 -1 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftHandRoll" -p "FBX_LeftHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".pa" -type "double3" 0 0 -21.412598770874361 ;
	setAttr ".bps" -type "matrix" 0.51118242614979126 -0.85896352392746578 0.029566733971181793 0
		 0.85913601576298215 0.51164215415911174 0.010373644794956321 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 5.5097646627003369 12.148202402262493 -0.31480962430229931 1;
	setAttr -l on ".amt" 1279017346;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 2.596201 2.596201 2.596201 ;
createNode joint -n "FBX_LeftElbowRoll" -p "FBX_LeftForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.3262893058653958e-31 1.1843548872543966e-16 1.1748840317954808e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 89.999999999999986 0 ;
	setAttr ".bps" -type "matrix" 0.033646552225579898 -0.033670905168914848 -0.99886644736342867 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 0.57712483042564056 -0.8153067575520313 0.046923567598473812 0
		 3.5547588056481416 14.909266941395517 -0.41734943117242157 1;
	setAttr -l on ".amt" 1276109186;
	setAttr ".aim" -type "double3" 1 1.3175224800043864e-14 -5.9211894646675081e-15 ;
	setAttr ".up" -type "double3" 1.3175224800043867e-14 -1 -7.8013002280645817e-29 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftElbowRoll_End" -p "FBX_LeftElbowRoll";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.29999999999999988 2.7829707478258147e-15 -3.1086244689504375e-15 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.033646552225579898 -0.033670905168914848 -0.99886644736342867 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 0.57712483042564056 -0.8153067575520313 0.046923567598473812 0
		 3.5648527713158162 14.899165669844846 -0.71700936538145021 1;
	setAttr -l on ".amt" 1276117378;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftForeArmRoll" -p "FBX_LeftForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.1282257310760708 1.0961885143939659e-15 -4.7610535965885447e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 4.2064274246655398 13.988912095017842 -0.38316949554904756 1;
	setAttr -l on ".amt" 1276141954;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftForeArmRoll1" -p "FBX_LeftForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 2.2564514621521417 2.1923770287879319e-15 -9.5221071931770894e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 4.8580960436829379 13.068557248640168 -0.34898955992567343 1;
	setAttr -l on ".amt" 1276150146;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube13" -p "FBX_LeftForeArm";
createNode joint -n "FBX_LeftArmRoll" -p "FBX_LeftArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.64363943585712535 -0.76264928926282138 0.063987015842547734 0
		 0.76398091207252428 0.64521625466751731 0.0053991389734481254 0 -0.045403112210011143 0.045409759961204263 0.99793612576252122 0
		 1.7763641343748549 17.016489334114837 -0.59414743587132335 1;
	setAttr -l on ".amt" 1276060034;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube14" -p "FBX_LeftArm";
createNode transform -n "pCube10" -p "FBX_LeftShoulder";
createNode joint -n "FBX_RightShoulder" -p "FBX_Spine3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.1036875399999999 0.59846639999999995 0.32383580439999998 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -165.63796686750371 -20.641262258508203 -99.156286258873024 ;
	setAttr ".bps" -type "matrix" 0.8316190850103562 0.34209624124803528 0.437469838012295 0
		 0.40812744490127795 -0.91070112399886538 -0.063682426661971298 0 0.37661875439878478 0.23150296860120162 -0.8969753003087314 0
		 -0.59846639999999873 17.501031350502242 0.025480877667486079 1;
	setAttr -l on ".amt" 1275912577;
	setAttr ".aim" -type "double3" -0.99999999999999989 2.9631835610548856e-10 1.5150533947098266e-10 ;
	setAttr ".up" -type "double3" -2.9631835610548861e-10 -1 4.4893813133245583e-20 ;
	setAttr ".dim" -type "double3" 8.451846 8.451846 8.451846 ;
createNode joint -n "FBX_RightArm" -p "FBX_RightShoulder";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -1.416390936 4.1969983040000001e-10 2.1459101160000001e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.17514848974987338 -22.090761571330116 -4.1975289240314364 ;
	setAttr ".bps" -type "matrix" 0.64363943560419168 0.76264928950381539 -0.063987015514421486 0
		 0.76398091227835474 -0.6452162544199771 -0.0053991394303281315 0 -0.045403112332199569 -0.045409759430992166 -0.9979361257810887 0
		 -1.7763641339611707 17.016489334826311 -0.59414743588572716 1;
	setAttr -l on ".amt" 1276051841;
	setAttr ".aim" -type "double3" -0.99999999999999989 -2.4895145486539835e-10 2.1374589934193421e-10 ;
	setAttr ".up" -type "double3" 2.489514548653984e-10 -1 -5.3212352612687526e-20 ;
	setAttr ".dim" -type "double3" 26.125045 26.125045 26.125045 ;
createNode joint -n "FBX_RightForeArm" -p "FBX_RightArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -2.7630293799999999 -6.8785510619999996e-10 5.9058447019999997e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.16126764777235425 0.0069461604192233911 0.032664452285442146 ;
	setAttr ".bps" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -3.5547588052144929 14.90926694170814 -0.41734943266651653 1;
	setAttr -l on ".amt" 1276100993;
	setAttr ".aim" -type "double3" -1 -2.4818958869571121e-10 1.7226285053713016e-10 ;
	setAttr ".up" -type "double3" 2.4818958869571121e-10 -1 -4.2753846022361107e-20 ;
	setAttr ".dim" -type "double3" 24.72653 24.72653 24.72653 ;
createNode joint -n "FBX_RightHand" -p "FBX_RightForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -3.3846771929999999 -8.4013862530000004e-10 5.8307136899999999e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 0 -9.083 ;
	setAttr ".bps" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -5.5097646620524738 12.148202402645275 -0.31480962735604656 1;
	setAttr -l on ".amt" 1276215681;
	setAttr ".aim" -type "double3" -1 -1.3013623694340461e-09 1.1162107426982644e-10 ;
	setAttr ".up" -type "double3" 1.3013623694340459e-09 -1 -1.4525946569055494e-19 ;
	setAttr ".dim" -type "double3" 2.596201 2.596201 2.596201 ;
createNode joint -n "FBX_RightHandThumb1" -p "FBX_RightHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.076525269009999994 -0.02354756987 -0.1983605728 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 5;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -36.162271620000027 -15.72646887000001 -18.234835150000006 ;
	setAttr ".bps" -type "matrix" 0.27578017443460623 0.91444587862297655 -0.29619930867284261 0
		 0.83216325407714753 -0.072905625717461064 0.54971728033824629 0 0.48109210547726811 -0.39808730802199299 -0.78107418420995833 0
		 -5.4800090072667711 12.228226723011417 -0.11867643066667788 1;
	setAttr -l on ".amt" 1276805505;
	setAttr ".aim" -type "double3" -1 -2.9849733202887242e-10 -3.0027398669227418e-10 ;
	setAttr ".up" -type "double3" -2.9849733202887247e-10 1 -8.9630983905316994e-20 ;
	setAttr ".dim" -type "double3" 4.827585 4.827585 4.827585 ;
createNode joint -n "FBX_RightHandThumb2" -p "FBX_RightHandThumb1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.78036916329999995 -2.329372251e-10 -2.343245598e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 1;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 86.433335060000005 -1.6818117029999999 5.2681824859999988 ;
	setAttr ".bps" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.6952193515516063 11.514621357937536 0.11246837606736199 1;
	setAttr -l on ".amt" 1276813697;
	setAttr ".aim" -type "double3" -1 -3.2432131205967545e-10 2.6209951514637986e-10 ;
	setAttr ".up" -type "double3" -3.243213120596755e-10 1 8.5004458642478708e-20 ;
	setAttr ".dim" -type "double3" 3.333332 3.333332 3.333332 ;
createNode joint -n "FBX_RightHandThumb3" -p "FBX_RightHandThumb2";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.35245262100000002 -1.1430856259999999e-10 9.2377661080000006e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 1;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.8238613231446372 11.200298372219118 0.20667641098735434 1;
	setAttr -l on ".amt" 1276821889;
	setAttr ".aim" -type "double3" -0.99999999999999989 -3.2332331751410391e-10 2.5952451920934321e-10 ;
	setAttr ".up" -type "double3" -3.2332331751410391e-10 1 8.3910328527017648e-20 ;
	setAttr ".dim" -type "double3" 3.333332 3.333332 3.333332 ;
createNode joint -n "FBX_RightHandThumb4" -p "FBX_RightHandThumb3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.3873306977 -1.2523138080000001e-10 1.005204808e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.9652334725952985 10.854870549846456 0.31020710339955365 1;
	setAttr -l on ".amt" 1276830081;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightHandMiddle0" -p "FBX_RightHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.1091541004 -8.4579454550000004e-11 1.21866961e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.97155148369999977 5.8958242000000149 8.6991533249999602 ;
	setAttr ".bps" -type "matrix" 0.69316755472423153 0.71720363443138879 0.071677666228999098 0
		 0.71991581661098081 -0.69376628260531203 -0.020237641002618153 0 0.035213038366121795 0.065629961743190926 -0.99722251782168114 0
		 -5.5728125964845789 12.059159489950932 -0.31150277131348342 1;
	setAttr -l on ".amt" 1276969345;
	setAttr ".aim" -type "double3" -1 -2.1081590002715558e-10 1.783375010839145e-10 ;
	setAttr ".up" -type "double3" -1.783375010839145e-10 -3.7596380799599271e-20 -1 ;
	setAttr ".dim" -type "double3" 4.438004 4.438004 4.438004 ;
createNode joint -n "FBX_RightHandMiddle1" -p "FBX_RightHandMiddle0";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.6780996601 -1.4295409300000001e-10 1.2093082090000001e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0.13342505950000072 -7.8431989480000892 -12.544067900000083 ;
	setAttr ".bps" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.0428492798340852 11.572823949327637 -0.36010737253783082 1;
	setAttr -l on ".amt" 1276977537;
	setAttr ".aim" -type "double3" -1 -3.5821284993810877e-10 1.0067975309124248e-10 ;
	setAttr ".up" -type "double3" -1.0067975309124248e-10 -3.6064781285879087e-20 -1 ;
	setAttr ".dim" -type "double3" 5.693803 5.693803 5.693803 ;
createNode joint -n "FBX_RightHandMiddle2" -p "FBX_RightHandMiddle1";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.35468834510000002 -1.2705569930000001e-10 3.5710101540000001e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.2273583745890555 11.270714534588636 -0.33796877211830534 1;
	setAttr -l on ".amt" 1276985729;
	setAttr ".aim" -type "double3" -0.99999999999999989 -3.3283778484435895e-10 8.5002129467414559e-11 ;
	setAttr ".up" -type "double3" -8.5002129467414559e-11 -2.8291920478987672e-20 -0.99999999999999989 ;
	setAttr ".dim" -type "double3" 3.589571 3.589571 3.589571 ;
createNode joint -n "FBX_RightHandMiddle3" -p "FBX_RightHandMiddle2";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.44035893059999998 -1.4656365009999999e-10 3.7431391319999998e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 2;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.4564333604781146 10.895634325051169 -0.31048286641313627 1;
	setAttr -l on ".amt" 1276993921;
	setAttr ".aim" -type "double3" -1 -3.3280485488419125e-10 8.5002150046518445e-11 ;
	setAttr ".up" -type "double3" -8.5002150046518445e-11 -2.8289128211075818e-20 -1 ;
	setAttr ".dim" -type "double3" 3.094458 3.094458 3.094458 ;
createNode joint -n "FBX_RightHandMiddle4" -p "FBX_RightHandMiddle3";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.62990893709999995 -2.0963852879999999e-10 5.3545612389999999e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.7841123760506212 10.359102964610553 -0.27116580833875431 1;
	setAttr -l on ".amt" 1277002113;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 0 -1 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightHandRoll" -p "FBX_RightHand";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -3.5955682879999998e-10 -5.7475801900000001e-11 0 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.51118242590695395 0.85896352408304311 -0.029566733649838542 0
		 0.85913601590258026 -0.51164215391656609 -0.010373645196271233 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -5.5097646623070533 12.148202402385188 -0.31480962734469387 1;
	setAttr -l on ".amt" 1279017345;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 0 -1 ;
	setAttr ".dim" -type "double3" 2.596201 2.596201 2.596201 ;
createNode joint -n "FBX_RightElbowRoll" -p "FBX_RightForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -1.359117263e-10 8.1712414610000005e-14 -1.6875389970000001e-14 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 89.999999999999986 0 ;
	setAttr ".bps" -type "matrix" 0.033646552376310451 0.033670904668845217 0.99886644737520836 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 0.57712483019291783 0.81530675773537364 -0.046923567275177894 0
		 -3.5547588052929293 14.90926694159722 -0.41734943266238284 1;
	setAttr -l on ".amt" 1276109185;
	setAttr ".aim" -type "double3" -1 3.7044676209676424e-10 1.7228588925869909e-10 ;
	setAttr ".up" -type "double3" -3.7044676209676419e-10 -0.99999999999999989 6.3822749830846756e-20 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightElbowRoll_End" -p "FBX_RightElbowRoll";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.3 1.111288839e-10 5.1685766779999998e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.033646552376310451 0.033670904668845217 0.99886644737520836 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 0.57712483019291783 0.81530675773537364 -0.046923567275177894 0
		 -3.5648527708853162 14.899165670174469 -0.71700936687825956 1;
	setAttr -l on ".amt" 1276117377;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightForeArmRoll" -p "FBX_RightForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -1.1282257309999999 -2.7998581230000002e-10 1.9434587269999999e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -4.2064274241604371 13.988912095353816 -0.38316949756301577 1;
	setAttr -l on ".amt" 1276141953;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightForeArmRoll1" -p "FBX_RightForeArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -2.2564514619999998 -5.6006399520000001e-10 3.8870950899999999e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -4.8580960431064568 13.068557248999547 -0.34898956245953205 1;
	setAttr -l on ".amt" 1276150145;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube15" -p "FBX_RightForeArm";
createNode joint -n "FBX_RightArmRoll" -p "FBX_RightArm";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -3.3256375430000002e-10 -2.593480986e-11 1.3505818690000001e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.64363943560419168 0.76264928950381539 -0.063987015514421486 0
		 0.76398091227835474 -0.6452162544199771 -0.0053991394303281315 0 -0.045403112332199569 -0.045409759430992166 -0.9979361257810887 0
		 -1.7763641342011676 17.016489334583284 -0.59414743599908681 1;
	setAttr -l on ".amt" 1276060033;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 -1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube12" -p "FBX_RightArm";
createNode transform -n "pCube11" -p "FBX_RightShoulder";
createNode transform -n "pCube9" -p "FBX_Spine2";
createNode transform -n "locator3" -p "FBX_Spine1";
createNode locator -n "locatorShape3" -p "locator3";
	setAttr -k off ".v";
createNode transform -n "pCube8" -p "FBX_Spine1";
createNode joint -n "FBX_LeftUpLeg" -p "FBX_Hips";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.85619999999999941 -0.40510070369043732 0.42465902716735693 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.062638657273618364 -11.565196345059224 -90.006683879452694 ;
	setAttr ".bps" -type "matrix" 0.031296508417216318 -0.99696735386587165 -0.071250430781667123 0
		 0.99950952055514963 0.031296508417216262 0.0011166380373579792 0 0.0011166380373579395 -0.071250430781667096 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr -l on ".amt" 1277116802;
	setAttr ".aim" -type "double3" 0.99999999999999989 2.1752260398789645e-17 -3.1842420251743824e-17 ;
	setAttr ".up" -type "double3" -2.1752260398789645e-17 1 6.9264461704362472e-34 ;
	setAttr ".dim" -type "double3" 38.596761 38.596761 38.596761 ;
createNode joint -n "FBX_LeftLeg" -p "FBX_LeftUpLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 5.1039432420868449 1.1584700213007615e-16 1.6653345369377348e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.044102829684610143 -3.514822238263049 0.0079926148885661741 ;
	setAttr ".bps" -type "matrix" -0.0086920160864499205 -0.99991250375181595 -0.0099716446551061655 0
		 0.99996222277549396 -0.008692016086449969 -4.3338743864050622e-05 0 -4.3338743864013325e-05 -0.0099716446551061308 0.99995028097632199 0
		 1.0159356026369648 5.6973087419301223 -0.36978490094438893 1;
	setAttr -l on ".amt" 1277165954;
	setAttr ".aim" -type "double3" 1 -4.8330246330195297e-17 -1.0241858841457402e-17 ;
	setAttr ".up" -type "double3" 4.8330246330195297e-17 1 -4.9499156068672477e-34 ;
	setAttr ".dim" -type "double3" 39.083986 39.083986 39.083986 ;
createNode joint -n "FBX_LeftFoot" -p "FBX_LeftLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 4.5943197435413126 1.3242089580900104e-17 -4.8572257327350599e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.0046139623211461159 -57.440408829989025 0.5019109038686862 ;
	setAttr ".bps" -type "matrix" -2.2975074100151094e-11 -0.54655416160175319 0.83742375678971792 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 2.3882337080172178e-12 0.83742375678971803 0.54655416160175319 0
		 0.97600170151980925 1.1033909841293275 -0.41559782485892144 1;
	setAttr -l on ".amt" 1277280642;
	setAttr ".aim" -type "double3" 0.99999999999999989 -6.6746522415144831e-17 4.7974062985885349e-17 ;
	setAttr ".up" -type "double3" 6.6746522415144831e-17 1 3.2021018704329663e-33 ;
	setAttr ".dim" -type "double3" 12.824393 12.824393 12.824393 ;
createNode joint -n "FBX_LeftToeBase" -p "FBX_LeftFoot";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.6633421254816507 5.0487097934144756e-28 5.5511151231257827e-17 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 -22.858324849999995 0 ;
	setAttr ".bps" -type "matrix" -2.0243081665677748e-11 -0.17833183310665823 0.98397040468746766 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 1.1125436388216179e-11 0.98397040468746777 0.17833183310665829 0
		 0.97600170148159382 0.19428442327982565 0.97732438668851707 1;
	setAttr -l on ".amt" 1277313410;
	setAttr ".aim" -type "double3" 0.99999999999999989 2.4702805348543419e-16 1.186892600730797e-16 ;
	setAttr ".up" -type "double3" -2.4702805348543419e-16 0.99999999999999989 -2.9319576885479347e-32 ;
	setAttr ".dim" -type "double3" 6.302893 6.302893 6.302893 ;
createNode joint -n "FBX_LeftToes_End" -p "FBX_LeftToeBase";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.89886392169674756 1.1102230246223798e-16 0 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -2.0243081665677748e-11 -0.17833183310665823 0.98397040468746766 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 1.1125436388216179e-11 0.98397040468746777 0.17833183310665829 0
		 0.97600170146339815 0.033988372410204942 1.8617798834794299 1;
	setAttr -l on ".amt" 1277329794;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftFootRoll" -p "FBX_LeftFoot";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -2.2975074100151094e-11 -0.54655416160175319 0.83742375678971792 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 2.3882337080172178e-12 0.83742375678971803 0.54655416160175319 0
		 0.97600170151980925 1.1033909841293275 -0.41559782485892144 1;
	setAttr -l on ".amt" 1279009154;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube7" -p "FBX_LeftFoot";
createNode joint -n "FBX_LeftKneeRoll" -p "FBX_LeftLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.9009795642339747e-16 1.6524790809532086e-18 1.8957551425785906e-18 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.0060453922723231399 -65.748234229989066 0.50353399139035637 ;
	setAttr ".bps" -type "matrix" -1.1678918682839212e-11 -0.41981816900806085 0.90760823319905992 0
		 1.0000000000000002 -2.5702877326505558e-12 1.1678892607776964e-11 0 -2.5702530381810362e-12 0.90760823319906014 0.41981816900806074 0
		 1.0159356026369648 5.6973087419301223 -0.36978490094438893 1;
	setAttr -l on ".amt" 1277174146;
	setAttr ".aim" -type "double3" 1 -3.7254561306925796e-16 -1.958774981215708e-15 ;
	setAttr ".up" -type "double3" 3.7254561306925796e-16 1 -7.2973302624173013e-31 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_LeftKneeRoll_End" -p "FBX_LeftKneeRoll";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 0.59601991577807734 1.8175355256292112e-27 -8.0491169285323849e-16 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -1.1678918682839212e-11 -0.41981816900806085 0.90760823319905992 0
		 1.0000000000000002 -2.5702877326505558e-12 1.1678892607776964e-11 0 -2.5702530381810362e-12 0.90760823319906014 0.41981816900806074 0
		 1.0159356026300039 5.44708875219583 0.17116768176640401 1;
	setAttr -l on ".amt" 1277182338;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "locator5" -p "FBX_LeftLeg";
createNode locator -n "locatorShape5" -p "locator5";
	setAttr -k off ".v";
createNode transform -n "pCube5" -p "FBX_LeftLeg";
createNode joint -n "FBX_LeftUpLegRoll" -p "FBX_LeftUpLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.031296508417216318 -0.99696735386587165 -0.071250430781667123 0
		 0.99950952055514963 0.031296508417216262 0.0011166380373579792 0 0.0011166380373579395 -0.071250430781667096 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr -l on ".amt" 1277124994;
	setAttr ".aim" -type "double3" 1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "locator2" -p "FBX_LeftUpLeg";
createNode locator -n "locatorShape2" -p "locator2";
	setAttr -k off ".v";
createNode transform -n "pCube3" -p "FBX_LeftUpLeg";
createNode joint -n "FBX_RightUpLeg" -p "FBX_Hips";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.8562 -0.40510070370000001 0.42465902719999998 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 179.93736134390082 11.565196345022338 90.006683879452751 ;
	setAttr ".bps" -type "matrix" 0.031296508417215763 0.99696735386587154 0.071250430781666735 0
		 0.99950952055517228 -0.031296508415754654 -0.0011166380578132027 0 0.0011166380168606271 0.071250430782308583 -0.99745783331069926 0
		 -0.85619999999999996 10.785773530257028 -0.0061267462316696997 1;
	setAttr -l on ".amt" 1277116801;
	setAttr ".aim" -type "double3" -1 -5.8513580473739752e-15 5.2465085344068179e-12 ;
	setAttr ".up" -type "double3" -5.8513580473739744e-15 0.99999999999999989 3.0699199933417576e-26 ;
	setAttr ".dim" -type "double3" 38.596761 38.596761 38.596761 ;
createNode joint -n "FBX_RightLeg" -p "FBX_RightUpLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -5.1039432419999997 -2.9864999360000001e-14 2.6777802200000001e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.044102829683689025 -3.5148222382179464 0.0079926148194405001 ;
	setAttr ".bps" -type "matrix" -0.0086920160889111357 0.99991250375177843 0.0099716446567102851 0
		 0.99996222277547142 0.008692016089114088 4.3338723526688185e-05 0 -4.3338764240070287e-05 0.009971644656533378 -0.999950280976307 0
		 -1.0159356026342443 5.697308742000601 -0.36978490093605609 1;
	setAttr -l on ".amt" 1277165953;
	setAttr ".aim" -type "double3" -1 -2.4580521629851605e-12 -4.8295461763317553e-13 ;
	setAttr ".up" -type "double3" -2.4580521629851605e-12 1 -1.1871276424968982e-24 ;
	setAttr ".dim" -type "double3" 39.083986 39.083986 39.083986 ;
createNode joint -n "FBX_RightFoot" -p "FBX_RightLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -4.5943197439999999 -1.129296656e-11 -2.2188917369999999e-12 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.0046139623209981379 -57.440408830000003 0.50191090390000392 ;
	setAttr ".bps" -type "matrix" -4.1179142561131865e-11 0.54655416160278825 -0.83742375678904257 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 -6.9664777418987356e-12 -0.83742375678904235 -0.54655416160278825 0
		 -0.97600170151308663 1.1033909837412104 -0.41559782486031394 1;
	setAttr -l on ".amt" 1277280641;
	setAttr ".aim" -type "double3" -0.99999999999999989 -2.0260973631506559e-11 -1.976003195942617e-10 ;
	setAttr ".up" -type "double3" -2.0260973631506559e-11 1 -4.0035748648766057e-21 ;
	setAttr ".dim" -type "double3" 12.824393 12.824393 12.824393 ;
createNode joint -n "FBX_RightToeBase" -p "FBX_RightFoot";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -1.663342125 -3.3700819910000002e-11 -3.2867686350000002e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr ".ro" 3;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" 0 -22.858324849999999 0 ;
	setAttr ".bps" -type "matrix" -4.0651425100040824e-11 0.17833183310787443 -0.9839704046872475 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 9.5768069592199499e-12 -0.98397040468724728 -0.17833183310787437 0
		 -0.97600170147829246 0.19428442342847696 0.97732438646229502 1;
	setAttr -l on ".amt" 1277313409;
	setAttr ".aim" -type "double3" -1 -2.0444165215858419e-11 1.1687852704544277e-10 ;
	setAttr ".up" -type "double3" -2.0444165215858422e-11 1 2.3894839171032086e-21 ;
	setAttr ".dim" -type "double3" 6.302805 6.302805 6.302805 ;
createNode joint -n "FBX_RightToes_End" -p "FBX_RightToeBase";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.89886392189999997 -1.8376633549999999e-11 1.0505785129999999e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -4.0651425100040824e-11 0.17833183310787443 -0.9839704046872475 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 9.5768069592199499e-12 -0.98397040468724728 -0.17833183310787437 0
		 -0.97600170146012899 0.03398837241814287 1.8617798834342691 1;
	setAttr -l on ".amt" 1277329793;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightFootRoll" -p "FBX_RightFoot";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 2.0874435509999999e-10 -3.3715252810000002e-12 -3.2691249709999998e-10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -4.1179142561131865e-11 0.54655416160278825 -0.83742375678904257 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 -6.9664777418987356e-12 -0.83742375678904235 -0.54655416160278825 0
		 -0.97600170151645815 1.1033909841290648 -0.41559782485644603 1;
	setAttr -l on ".amt" 1279009153;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "pCube6" -p "FBX_RightFoot";
createNode joint -n "FBX_RightKneeRoll" -p "FBX_RightLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -7.0798478190000004e-11 6.5503158450000003e-15 4.3484105210000001e-12 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".jo" -type "double3" -0.0060453922720041676 -65.74823423000025 0.50353399140000554 ;
	setAttr ".bps" -type "matrix" -3.1198601428000794e-11 0.41981816900917912 -0.90760823319854267 0
		 0.99999999999999989 5.0611251301013738e-12 -3.2033465615331769e-11 0 -8.8546687343482589e-12 -0.90760823319854256 -0.41981816900917912 0
		 -1.0159356026336226 5.6973087419298523 -0.36978490094111027 1;
	setAttr -l on ".amt" 1277174145;
	setAttr ".aim" -type "double3" -1 -1.9552311409994707e-11 -1.0625932248377075e-12 ;
	setAttr ".up" -type "double3" -1.9552311409994707e-11 1 -2.0776153634177379e-23 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode joint -n "FBX_RightKneeRoll_End" -p "FBX_RightKneeRoll";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" -0.59601991580000002 -1.1653567000000001e-11 -6.323830348e-13 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" -3.1198601428000794e-11 0.41981816900917912 -0.90760823319854267 0
		 0.99999999999999989 5.0611251301013738e-12 -3.2033465615331769e-11 0 -8.8546687343482589e-12 -0.90760823319854256 -0.41981816900917912 0
		 -1.0159356026266813 5.4470887521862652 0.17116768178953734 1;
	setAttr -l on ".amt" 1277182337;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "locator4" -p "FBX_RightLeg";
createNode locator -n "locatorShape4" -p "locator4";
	setAttr -k off ".v";
createNode transform -n "pCube4" -p "FBX_RightLeg";
createNode joint -n "FBX_RightUpLegRoll" -p "FBX_RightUpLeg";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	addAttr -ci true -sn "aim" -ln "aim" -at "double3" -nc 3;
	addAttr -ci true -sn "aimX" -ln "aimX" -at "double" -p "aim";
	addAttr -ci true -sn "aimY" -ln "aimY" -at "double" -p "aim";
	addAttr -ci true -sn "aimZ" -ln "aimZ" -at "double" -p "aim";
	addAttr -ci true -sn "up" -ln "up" -at "double3" -nc 3;
	addAttr -ci true -sn "upX" -ln "upX" -at "double" -p "up";
	addAttr -ci true -sn "upY" -ln "upY" -at "double" -p "up";
	addAttr -ci true -sn "upZ" -ln "upZ" -at "double" -p "up";
	addAttr -ci true -sn "dim" -ln "dimension" -at "double3" -nc 3;
	addAttr -ci true -sn "dimensionX" -ln "dimensionX" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionY" -ln "dimensionY" -at "double" -p "dimension";
	addAttr -ci true -sn "dimensionZ" -ln "dimensionZ" -at "double" -p "dimension";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -bt "lock" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr ".t" -type "double3" 1.5912604569999999e-11 -3.1197266989999997e-14 3.0063063150000003e-11 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".bps" -type "matrix" 0.031296508417215763 0.99696735386587154 0.071250430781666735 0
		 0.99950952055517228 -0.031296508415754654 -0.0011166380578132027 0 0.0011166380168606271 0.071250430782308583 -0.99745783331069926 0
		 -0.85619999999949958 10.785773530275037 -0.0061267462605225226 1;
	setAttr -l on ".amt" 1277124993;
	setAttr ".aim" -type "double3" -1 0 0 ;
	setAttr ".up" -type "double3" 0 1 0 ;
	setAttr ".dim" -type "double3" 1 1 1 ;
createNode transform -n "locator1" -p "FBX_RightUpLeg";
createNode locator -n "locatorShape1" -p "locator1";
	setAttr -k off ".v";
createNode transform -n "pCube2" -p "FBX_RightUpLeg";
createNode transform -n "pCube1" -p "FBX_Hips";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube1";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube2";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube3";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube4";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube5";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube6";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube7";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube8";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube9";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube10";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube11";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube12";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube13";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube14";
parent -s -nc -r -add "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1" "pCube15";
createNode lightLinker -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode displayLayerManager -n "layerManager";
	setAttr ".cdl" 2;
	setAttr -s 4 ".dli[1:3]"  3 5 2;
	setAttr -s 3 ".dli";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode displayLayer -n "MODEL";
	setAttr ".c" 15;
	setAttr ".do" 2;
createNode displayLayer -n "SKELETON";
	setAttr ".c" 4;
	setAttr ".do" 1;
createNode script -n "uiConfigurationScriptNode";
	setAttr ".b" -type "string" (
		"// Maya Mel UI Configuration File.\n//\n//  This script is machine generated.  Edit at your own risk.\n//\n//\n\nglobal string $gMainPane;\nif (`paneLayout -exists $gMainPane`) {\n\n\tglobal int $gUseScenePanelConfig;\n\tint    $useSceneConfig = $gUseScenePanelConfig;\n\tint    $menusOkayInPanels = `optionVar -q allowMenusInPanels`;\tint    $nVisPanes = `paneLayout -q -nvp $gMainPane`;\n\tint    $nPanes = 0;\n\tstring $editorName;\n\tstring $panelName;\n\tstring $itemFilterName;\n\tstring $panelConfig;\n\n\t//\n\t//  get current state of the UI\n\t//\n\tsceneUIReplacement -update $gMainPane;\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Top View\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"top\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"wireframe\" \n"
		+ "                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -rendererName \"base_OpenGL_Renderer\" \n                -colorResolution 256 256 \n"
		+ "                -bumpResolution 512 512 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 1\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n"
		+ "                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"top\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"wireframe\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n"
		+ "            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -rendererName \"base_OpenGL_Renderer\" \n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n"
		+ "            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Side View\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"side\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"wireframe\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n"
		+ "                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -rendererName \"base_OpenGL_Renderer\" \n                -colorResolution 256 256 \n                -bumpResolution 512 512 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 1\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n"
		+ "                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"side\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"wireframe\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n"
		+ "            -rendererName \"base_OpenGL_Renderer\" \n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -fluids 1\n"
		+ "            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Front View\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"front\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"wireframe\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n"
		+ "                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -rendererName \"base_OpenGL_Renderer\" \n                -colorResolution 256 256 \n                -bumpResolution 512 512 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n"
		+ "                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 1\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n"
		+ "                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"front\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"wireframe\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n"
		+ "            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -rendererName \"base_OpenGL_Renderer\" \n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n"
		+ "            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Persp View\")) `;\n\tif (\"\" == $panelName) {\n"
		+ "\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n"
		+ "                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -rendererName \"base_OpenGL_Renderer\" \n                -colorResolution 256 256 \n                -bumpResolution 512 512 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 1\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n"
		+ "                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"persp\" \n"
		+ "            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -rendererName \"base_OpenGL_Renderer\" \n            -colorResolution 256 256 \n"
		+ "            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n"
		+ "            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `outlinerPanel -unParent -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            outlinerEditor -e \n                -showShapes 0\n                -showAttributes 0\n                -showConnected 0\n                -showAnimCurvesOnly 0\n                -showMuteInfo 0\n                -autoExpand 0\n                -showDagOnly 1\n                -ignoreDagHierarchy 0\n                -expandConnections 0\n                -showUnitlessCurves 1\n                -showCompounds 1\n"
		+ "                -showLeafs 1\n                -showNumericAttrsOnly 0\n                -highlightActive 1\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"defaultSetFilter\" \n                -showSetMembers 1\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -autoExpand 0\n            -showDagOnly 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n"
		+ "            -attrAlphaOrder \"default\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"graphEditor\" -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -autoExpand 1\n                -showDagOnly 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n"
		+ "                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayKeys 1\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 1\n"
		+ "                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showResults \"off\" \n                -showBufferCurves \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -autoExpand 1\n                -showDagOnly 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n"
		+ "                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayKeys 1\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 1\n"
		+ "                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showResults \"off\" \n                -showBufferCurves \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"dopeSheetPanel\" -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -autoExpand 0\n"
		+ "                -showDagOnly 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUnitlessCurves 0\n                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n"
		+ "                -showNamespace 1\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayKeys 1\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 0\n                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 0\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n"
		+ "                -showMuteInfo 0\n                -autoExpand 0\n                -showDagOnly 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUnitlessCurves 0\n                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n"
		+ "                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayKeys 1\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 0\n                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 0\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"clipEditorPanel\" -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels `;\n"
		+ "\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayKeys 0\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 0\n                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayKeys 0\n                -displayTangents 0\n                -displayActiveKeys 0\n                -displayActiveKeyTangents 0\n                -displayInfinities 0\n                -autoFit 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperGraphPanel\" (localizedPanelLabel(\"Hypergraph\")) `;\n"
		+ "\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"hyperGraphPanel\" -l (localizedPanelLabel(\"Hypergraph\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -zoom 1\n                -animateTransition 0\n                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -freeform 0\n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n"
		+ "                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypergraph\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -zoom 1\n                -animateTransition 0\n                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -freeform 0\n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n"
		+ "                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperShadePanel\" (localizedPanelLabel(\"Hypershade\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"hyperShadePanel\" -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"visorPanel\" (localizedPanelLabel(\"Visor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"visorPanel\" -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"polyTexturePlacementPanel\" (localizedPanelLabel(\"UV Texture Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"polyTexturePlacementPanel\" -l (localizedPanelLabel(\"UV Texture Editor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"UV Texture Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"multiListerPanel\" (localizedPanelLabel(\"Multilister\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"multiListerPanel\" -l (localizedPanelLabel(\"Multilister\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Multilister\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"renderWindowPanel\" (localizedPanelLabel(\"Render View\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"renderWindowPanel\" -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"blendShapePanel\" (localizedPanelLabel(\"Blend Shape\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\tblendShapePanel -unParent -l (localizedPanelLabel(\"Blend Shape\")) -mbv $menusOkayInPanels ;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tblendShapePanel -edit -l (localizedPanelLabel(\"Blend Shape\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynRelEdPanel\" (localizedPanelLabel(\"Dynamic Relationships\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"dynRelEdPanel\" -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"devicePanel\" (localizedPanelLabel(\"Devices\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\tdevicePanel -unParent -l (localizedPanelLabel(\"Devices\")) -mbv $menusOkayInPanels ;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tdevicePanel -edit -l (localizedPanelLabel(\"Devices\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"relationshipPanel\" (localizedPanelLabel(\"Relationship Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"relationshipPanel\" -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"referenceEditorPanel\" (localizedPanelLabel(\"Reference Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"referenceEditorPanel\" -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"componentEditorPanel\" (localizedPanelLabel(\"Component Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"componentEditorPanel\" -l (localizedPanelLabel(\"Component Editor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Component Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynPaintScriptedPanelType\" (localizedPanelLabel(\"Paint Effects\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"dynPaintScriptedPanelType\" -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"scriptEditorPanel\" (localizedPanelLabel(\"Script Editor\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `scriptedPanel -unParent  -type \"scriptEditorPanel\" -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels `;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\tif ($useSceneConfig) {\n\t\tscriptedPanel -e -to $panelName;\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Model Panel12\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Model Panel12\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"persp\" \n                -useInteractiveMode 0\n"
		+ "                -displayLights \"default\" \n                -displayAppearance \"wireframe\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n"
		+ "                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 0\n                -polymeshes 0\n                -subdivSurfaces 0\n                -planes 0\n                -lights 0\n                -cameras 0\n                -controlVertices 1\n                -hulls 1\n                -grid 0\n                -joints 0\n                -ikHandles 0\n                -deformers 0\n"
		+ "                -dynamics 0\n                -fluids 0\n                -hairSystems 0\n                -follicles 0\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 0\n                -manipulators 1\n                -dimensions 0\n                -handles 0\n                -pivots 0\n                -textures 0\n                -strokes 0\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Model Panel12\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"wireframe\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n"
		+ "            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -colorResolution 4 4 \n            -bumpResolution 4 4 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 0\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n"
		+ "            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 0\n            -polymeshes 0\n            -subdivSurfaces 0\n            -planes 0\n            -lights 0\n            -cameras 0\n            -controlVertices 1\n            -hulls 1\n            -grid 0\n            -joints 0\n            -ikHandles 0\n            -deformers 0\n            -dynamics 0\n            -fluids 0\n            -hairSystems 0\n            -follicles 0\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 0\n            -manipulators 1\n            -dimensions 0\n            -handles 0\n            -pivots 0\n            -textures 0\n            -strokes 0\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Model Panel19\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Model Panel19\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n"
		+ "                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n"
		+ "                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 0\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 0\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 0\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Model Panel19\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n"
		+ "            -colorResolution 4 4 \n            -bumpResolution 4 4 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 0\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 0\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n"
		+ "            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 0\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 0\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `outlinerPanel -unParent -l (localizedPanelLabel(\"\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            outlinerEditor -e \n                -showShapes 0\n                -showAttributes 0\n                -showConnected 0\n                -showAnimCurvesOnly 0\n                -showMuteInfo 0\n                -autoExpand 0\n                -showDagOnly 1\n                -ignoreDagHierarchy 0\n                -expandConnections 0\n                -showUnitlessCurves 1\n"
		+ "                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 0\n                -highlightActive 1\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"defaultSetFilter\" \n                -showSetMembers 1\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -autoExpand 0\n            -showDagOnly 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n"
		+ "            -attrAlphaOrder \"default\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Model Panel34\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Model Panel34\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n"
		+ "                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -maxConstantTransparency 1\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n"
		+ "                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -joints 0\n                -ikHandles 1\n                -deformers 1\n                -dynamics 0\n                -fluids 0\n                -hairSystems 0\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 0\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 0\n                -textures 1\n"
		+ "                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Model Panel34\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n"
		+ "            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -colorResolution 4 4 \n            -bumpResolution 4 4 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 0\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n"
		+ "            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -joints 0\n            -ikHandles 1\n            -deformers 1\n            -dynamics 0\n            -fluids 0\n            -hairSystems 0\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 0\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 0\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Model Panel41\")) `;\n\tif (\"\" == $panelName) {\n\t\tif ($useSceneConfig) {\n\t\t\t$panelName = `modelPanel -unParent -l (localizedPanelLabel(\"Model Panel41\")) -mbv $menusOkayInPanels `;\n\t\t\t$editorName = $panelName;\n            modelEditor -e \n                -camera \"persp\" \n"
		+ "                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 8192\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n"
		+ "                -maxConstantTransparency 1\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 0\n                -joints 0\n"
		+ "                -ikHandles 0\n                -deformers 1\n                -dynamics 0\n                -fluids 0\n                -hairSystems 0\n                -follicles 1\n                -nCloths 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 0\n                -manipulators 1\n                -dimensions 1\n                -handles 1\n                -pivots 0\n                -textures 1\n                -strokes 1\n                -shadows 0\n                $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n\t\t}\n\t} else {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Model Panel41\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -selectionHiliteDisplay 1\n"
		+ "            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 8192\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -maxConstantTransparency 1\n            -colorResolution 4 4 \n            -bumpResolution 4 4 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 0\n            -occlusionCulling 0\n"
		+ "            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 0\n            -joints 0\n            -ikHandles 0\n            -deformers 1\n            -dynamics 0\n            -fluids 0\n            -hairSystems 0\n            -follicles 1\n            -nCloths 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 0\n            -manipulators 1\n            -dimensions 1\n            -handles 1\n            -pivots 0\n            -textures 1\n            -strokes 1\n            -shadows 0\n            $editorName;\nmodelEditor -e -viewSelected 0 $editorName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n\t\t\t\t-defaultImage \"vacantCell.xpm\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n\t\t\t\t-removeAllPanels\n\t\t\t\t-ap false\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 1\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 8192\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -maxConstantTransparency 1\\n    -rendererName \\\"base_OpenGL_Renderer\\\" \\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -shadows 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 1\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 8192\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -maxConstantTransparency 1\\n    -rendererName \\\"base_OpenGL_Renderer\\\" \\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -shadows 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        setFocus `paneLayout -q -p1 $gMainPane`;\n        sceneUIReplacement -deleteRemaining;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 0 -max 3900 -ast 0 -aet 3900 ";
	setAttr ".st" 6;
createNode dagPose -n "FBX_AMFlexStance";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	setAttr -s 100 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[2]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[3]" -type "matrix" 1 0 0 0 0 0.96292280248626105 0.26977708659559096 0
		 0 -0.26977708659559096 0.96292280248626105 0 0 11.290417510307522 -0.30575371918217331 1
		;
	setAttr ".wm[4]" -type "matrix" 2.2204460492503131e-16 0.99509301942264905 0.098943836070343738 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.3877787807814454e-17 -0.098943836070343738 0.99509301942264905 0
		 0 11.996189775258431 -0.10802116476886733 1;
	setAttr ".wm[5]" -type "matrix" 2.1316951863865569e-16 0.99172106330715759 -0.128410796247513 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.3680105952454152e-17 0.128410796247513 0.99172106330715759 0
		 3.565817171172828e-16 13.594210937163945 0.05087286904945576 1;
	setAttr ".wm[6]" -type "matrix" 2.113254464861858e-16 0.98778726979368714 -0.15580856726615877 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.9555411278822762e-17 0.15580856726615877 0.98778726979368714 0
		 7.0392436188590434e-16 15.210140921908927 -0.15836223112010339 1;
	setAttr ".wm[7]" -type "matrix" 2.209797897348894e-16 0.99896907691404224 0.045395851897569228 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.5774640627485565e-17 -0.045395851897569228 0.99896907691404224 0
		 9.6130091607533248e-16 16.413182429682582 -0.34812391303273083 1;
	setAttr ".wm[8]" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr ".wm[9]" -type "matrix" 2.1898562510217626e-16 0.99987373456677664 -0.01589071815515776 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 3.9264431351556042e-17 0.01589071815515776 0.99987373456677664 0
		 1.4120088374132143e-15 18.440282855871136 -0.19179676487531067 1;
	setAttr ".wm[10]" -type "matrix" 2.2115826839442644e-16 0.99861931185935604 0.052530657539630252 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr ".wm[11]" -type "matrix" 2.2115826839442644e-16 0.99861931185935604 0.052530657539630252 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 1.9332146147797686e-15 20.805825981758147 -0.14217948243763939 1;
	setAttr ".wm[12]" -type "matrix" -2.1353245134360761e-16 -0.99244361258999347 0.1227015722365561 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -6.2452316161546887e-17 -0.1227015722365561 -0.99244361258999347 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[13]" -type "matrix" 0.83161908486574476 -0.34209624156754381 -0.43746983803734568 0
		 0.40812744501784315 0.91070112398666447 0.063682426089405872 0 0.37661875459178623 -0.23150296817705379 0.89697530033716399 0
		 0.59846640000000095 17.501031350061492 0.025480877690902903 1;
	setAttr ".wm[14]" -type "matrix" 0.64363943585712535 -0.76264928926282138 0.063987015842547734 0
		 0.76398091207252428 0.64521625466751731 0.0053991389734481254 0 -0.045403112210011143 0.045409759961204263 0.99793612576252122 0
		 1.7763641343748549 17.016489334114837 -0.59414743587132335 1;
	setAttr ".wm[15]" -type "matrix" 0.64363943585712535 -0.76264928926282138 0.063987015842547734 0
		 0.76398091207252428 0.64521625466751731 0.0053991389734481254 0 -0.045403112210011143 0.045409759961204263 0.99793612576252122 0
		 1.7763641343748549 17.016489334114837 -0.59414743587132335 1;
	setAttr ".wm[16]" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 3.5547588056481416 14.909266941395517 -0.41734943117242168 1;
	setAttr ".wm[17]" -type "matrix" 0.033646552225579898 -0.033670905168914848 -0.99886644736342867 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 0.57712483042564056 -0.8153067575520313 0.046923567598473812 0
		 3.5547588056481416 14.909266941395517 -0.41734943117242157 1;
	setAttr ".wm[18]" -type "matrix" 0.033646552225579898 -0.033670905168914848 -0.99886644736342867 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 0.57712483042564056 -0.8153067575520313 0.046923567598473812 0
		 3.5648527713158162 14.899165669844846 -0.71700936538145021 1;
	setAttr ".wm[19]" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 0.29225669056177278 19.851563453626383 0.41745445901943362 1;
	setAttr ".wm[20]" -type "matrix" 0.031296508417216318 -0.99696735386587165 -0.071250430781667123 0
		 0.99950952055514963 0.031296508417216262 0.0011166380373579792 0 0.0011166380373579395 -0.071250430781667096 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr ".wm[21]" -type "matrix" -0.0086920160864499205 -0.99991250375181595 -0.0099716446551061655 0
		 0.99996222277549396 -0.008692016086449969 -4.3338743864050622e-05 0 -4.3338743864013325e-05 -0.0099716446551061308 0.99995028097632199 0
		 1.0159356026369648 5.6973087419301223 -0.36978490094438893 1;
	setAttr ".wm[22]" -type "matrix" -2.2975074100151094e-11 -0.54655416160175319 0.83742375678971792 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 2.3882337080172178e-12 0.83742375678971803 0.54655416160175319 0
		 0.97600170151980925 1.1033909841293275 -0.41559782485892144 1;
	setAttr ".wm[23]" -type "matrix" -2.2975074100151094e-11 -0.54655416160175319 0.83742375678971792 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 2.3882337080172178e-12 0.83742375678971803 0.54655416160175319 0
		 0.97600170151980925 1.1033909841293275 -0.41559782485892144 1;
	setAttr ".wm[24]" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 4.2064274246655398 13.988912095017842 -0.38316949554904756 1;
	setAttr ".wm[25]" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 4.8580960436829379 13.068557248640168 -0.34898955992567343 1;
	setAttr ".wm[26]" -type "matrix" 0.57760481884760217 -0.81575417137478856 0.030295298788101804 0
		 0.81596252342218911 0.57804944532029301 0.0079999459619548227 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 5.5097646627003369 12.148202402262493 -0.31480962430229931 1;
	setAttr ".wm[27]" -type "matrix" 0.69316755490681126 -0.71720363427704981 -0.071677666007649674 0
		 0.7199158164255508 0.69376628281126029 0.020237640538819459 0 0.035213038563080321 -0.06562996125275157 0.99722251784700344 0
		 5.5728125968573092 12.059159489864832 -0.31150276822885303 1;
	setAttr ".wm[28]" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.042849280288344 11.572823949180748 -0.36010736919123121 1;
	setAttr ".wm[29]" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.2273583750410744 11.270714534454719 -0.3379687686251196 1;
	setAttr ".wm[30]" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.4564333609062823 10.895634324989402 -0.31048286274848064 1;
	setAttr ".wm[31]" -type "matrix" 0.52020061359023839 -0.85176019709208073 0.062417051115849886 0
		 0.85319384726462555 0.52155332049814207 0.0065109805059193858 0 -0.038099614304158341 0.049866827922191374 0.99802891684702832 0
		 6.7841123765150781 10.359102964536724 -0.27116580442037141 1;
	setAttr ".wm[32]" -type "matrix" 0.51118242614979126 -0.85896352392746578 0.029566733971181793 0
		 0.85913601576298215 0.51164215415911174 0.010373644794956321 0 -0.024038169949512318 0.020099021108823167 0.9995089773163347 0
		 5.5097646627003369 12.148202402262493 -0.31480962430229931 1;
	setAttr ".wm[33]" -type "matrix" 0.27578017479248546 -0.91444587836227009 0.29619930914450476 0
		 0.83216325399207891 0.07290562571281739 -0.54971728046763901 0 0.48109210541926434 0.39808730862171193 0.78107418394002814 0
		 5.4800090076208514 12.228226722954085 -0.11867642768531272 1;
	setAttr ".wm[34]" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.6952193518774239 11.514621357976598 0.1124683793607818 1;
	setAttr ".wm[35]" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.8238613234834604 11.200298372243006 0.20667641443037332 1;
	setAttr ".wm[36]" -type "matrix" 0.36499082123372906 -0.89181628097930765 0.26729276345491315 0
		 0.51964607801572393 0.43336146654484448 0.73631908362949383 0 -0.77249573074419231 -0.12985207081266537 0.62160179028672224 0
		 5.9652334728945267 10.854870549988012 0.31020710696646492 1;
	setAttr ".wm[37]" -type "matrix" -1.1678918682839212e-11 -0.41981816900806085 0.90760823319905992 0
		 1.0000000000000002 -2.5702877326505558e-12 1.1678892607776964e-11 0 -2.5702530381810362e-12 0.90760823319906014 0.41981816900806074 0
		 1.0159356026369648 5.6973087419301223 -0.36978490094438893 1;
	setAttr ".wm[38]" -type "matrix" -1.1678918682839212e-11 -0.41981816900806085 0.90760823319905992 0
		 1.0000000000000002 -2.5702877326505558e-12 1.1678892607776964e-11 0 -2.5702530381810362e-12 0.90760823319906014 0.41981816900806074 0
		 1.0159356026300039 5.44708875219583 0.17116768176640401 1;
	setAttr ".wm[39]" -type "matrix" -2.0243081665677748e-11 -0.17833183310665823 0.98397040468746766 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 1.1125436388216179e-11 0.98397040468746777 0.17833183310665829 0
		 0.97600170148159382 0.19428442327982565 0.97732438668851707 1;
	setAttr ".wm[40]" -type "matrix" -2.0243081665677748e-11 -0.17833183310665823 0.98397040468746766 0
		 1.0000000000000002 -1.4557135011306066e-11 1.7934545301222411e-11 0 1.1125436388216179e-11 0.98397040468746777 0.17833183310665829 0
		 0.97600170146339815 0.033988372410204942 1.8617798834794299 1;
	setAttr ".wm[41]" -type "matrix" 0.031296508417216318 -0.99696735386587165 -0.071250430781667123 0
		 0.99950952055514963 0.031296508417216262 0.0011166380373579792 0 0.0011166380373579395 -0.071250430781667096 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr ".wm[42]" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr ".wm[43]" -type "matrix" 0.8316190850103562 0.34209624124803528 0.437469838012295 0
		 0.40812744490127795 -0.91070112399886538 -0.063682426661971298 0 0.37661875439878478 0.23150296860120162 -0.8969753003087314 0
		 -0.59846639999999873 17.501031350502242 0.025480877667486079 1;
	setAttr ".wm[44]" -type "matrix" 0.64363943560419168 0.76264928950381539 -0.063987015514421486 0
		 0.76398091227835474 -0.6452162544199771 -0.0053991394303281315 0 -0.045403112332199569 -0.045409759430992166 -0.9979361257810887 0
		 -1.7763641339611707 17.016489334826311 -0.59414743588572716 1;
	setAttr ".wm[45]" -type "matrix" 0.64363943560419168 0.76264928950381539 -0.063987015514421486 0
		 0.76398091227835474 -0.6452162544199771 -0.0053991394303281315 0 -0.045403112332199569 -0.045409759430992166 -0.9979361257810887 0
		 -1.7763641342011676 17.016489334583284 -0.59414743599908681 1;
	setAttr ".wm[46]" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -3.5547588052144929 14.90926694170814 -0.41734943266651653 1;
	setAttr ".wm[47]" -type "matrix" 0.033646552376310451 0.033670904668845217 0.99886644737520836 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 0.57712483019291783 0.81530675773537364 -0.046923567275177894 0
		 -3.5547588052929293 14.90926694159722 -0.41734943266238284 1;
	setAttr ".wm[48]" -type "matrix" 0.033646552376310451 0.033670904668845217 0.99886644737520836 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 0.57712483019291783 0.81530675773537364 -0.046923567275177894 0
		 -3.5648527708853162 14.899165670174469 -0.71700936687825956 1;
	setAttr ".wm[49]" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 -0.29144088923930972 19.851563453626383 0.41745445901943362 1;
	setAttr ".wm[50]" -type "matrix" 0.031296508417215763 0.99696735386587154 0.071250430781666735 0
		 0.99950952055517228 -0.031296508415754654 -0.0011166380578132027 0 0.0011166380168606271 0.071250430782308583 -0.99745783331069926 0
		 -0.85619999999999996 10.785773530257028 -0.0061267462316696997 1;
	setAttr ".wm[51]" -type "matrix" -0.0086920160889111357 0.99991250375177843 0.0099716446567102851 0
		 0.99996222277547142 0.008692016089114088 4.3338723526688185e-05 0 -4.3338764240070287e-05 0.009971644656533378 -0.999950280976307 0
		 -1.0159356026342443 5.697308742000601 -0.36978490093605609 1;
	setAttr ".wm[52]" -type "matrix" -4.1179142561131865e-11 0.54655416160278825 -0.83742375678904257 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 -6.9664777418987356e-12 -0.83742375678904235 -0.54655416160278825 0
		 -0.97600170151308663 1.1033909837412104 -0.41559782486031394 1;
	setAttr ".wm[53]" -type "matrix" -4.1179142561131865e-11 0.54655416160278825 -0.83742375678904257 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 -6.9664777418987356e-12 -0.83742375678904235 -0.54655416160278825 0
		 -0.97600170151645815 1.1033909841290648 -0.41559782485644603 1;
	setAttr ".wm[54]" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -4.2064274241604371 13.988912095353816 -0.38316949756301577 1;
	setAttr ".wm[55]" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -4.8580960431064568 13.068557248999547 -0.34898956245953205 1;
	setAttr ".wm[56]" -type "matrix" 0.57760481861658086 0.81575417154908236 -0.030295298499544071 0
		 0.81596252358057708 -0.57804944509082778 -0.0079999463874540315 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -5.5097646620524738 12.148202402645275 -0.31480962735604656 1;
	setAttr ".wm[57]" -type "matrix" 0.69316755472423153 0.71720363443138879 0.071677666228999098 0
		 0.71991581661098081 -0.69376628260531203 -0.020237641002618153 0 0.035213038366121795 0.065629961743190926 -0.99722251782168114 0
		 -5.5728125964845789 12.059159489950932 -0.31150277131348342 1;
	setAttr ".wm[58]" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.0428492798340852 11.572823949327637 -0.36010737253783082 1;
	setAttr ".wm[59]" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.2273583745890555 11.270714534588636 -0.33796877211830534 1;
	setAttr ".wm[60]" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.4564333604781146 10.895634325051169 -0.31048286641313627 1;
	setAttr ".wm[61]" -type "matrix" 0.52020061328259048 0.85176019730310493 -0.062417050800178397 0
		 0.85319384744517168 -0.52155332019781764 -0.0065109809044386398 0 -0.038099614461590083 -0.049866827458824668 -0.99802891686417083 0
		 -6.7841123760506212 10.359102964610553 -0.27116580833875431 1;
	setAttr ".wm[62]" -type "matrix" 0.51118242590695395 0.85896352408304311 -0.029566733649838542 0
		 0.85913601590258026 -0.51164215391656609 -0.010373645196271233 0 -0.024038170124256863 -0.020099020634247036 -0.99950897732167532 0
		 -5.5097646623070533 12.148202402385188 -0.31480962734469387 1;
	setAttr ".wm[63]" -type "matrix" 0.27578017443460623 0.91444587862297655 -0.29619930867284261 0
		 0.83216325407714753 -0.072905625717461064 0.54971728033824629 0 0.48109210547726811 -0.39808730802199299 -0.78107418420995833 0
		 -5.4800090072667711 12.228226723011417 -0.11867643066667788 1;
	setAttr ".wm[64]" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.6952193515516063 11.514621357937536 0.11246837606736199 1;
	setAttr ".wm[65]" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.8238613231446372 11.200298372219118 0.20667641098735434 1;
	setAttr ".wm[66]" -type "matrix" 0.36499082088616325 0.89181628125826984 -0.26729276299876598 0
		 0.51964607806766216 -0.43336146594605124 -0.73631908394525958 0 -0.77249573087347312 0.12985207089515027 -0.62160179010882755 0
		 -5.9652334725952985 10.854870549846456 0.31020710339955365 1;
	setAttr ".wm[67]" -type "matrix" -3.1198601428000794e-11 0.41981816900917912 -0.90760823319854267 0
		 0.99999999999999989 5.0611251301013738e-12 -3.2033465615331769e-11 0 -8.8546687343482589e-12 -0.90760823319854256 -0.41981816900917912 0
		 -1.0159356026336226 5.6973087419298523 -0.36978490094111027 1;
	setAttr ".wm[68]" -type "matrix" -3.1198601428000794e-11 0.41981816900917912 -0.90760823319854267 0
		 0.99999999999999989 5.0611251301013738e-12 -3.2033465615331769e-11 0 -8.8546687343482589e-12 -0.90760823319854256 -0.41981816900917912 0
		 -1.0159356026266813 5.4470887521862652 0.17116768178953734 1;
	setAttr ".wm[69]" -type "matrix" -4.0651425100040824e-11 0.17833183310787443 -0.9839704046872475 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 9.5768069592199499e-12 -0.98397040468724728 -0.17833183310787437 0
		 -0.97600170147829246 0.19428442342847696 0.97732438646229502 1;
	setAttr ".wm[70]" -type "matrix" -4.0651425100040824e-11 0.17833183310787443 -0.9839704046872475 0
		 0.99999999999999989 1.6672692740304917e-11 -3.8291958999784291e-11 0 9.5768069592199499e-12 -0.98397040468724728 -0.17833183310787437 0
		 -0.97600170146012899 0.03398837241814287 1.8617798834342691 1;
	setAttr ".wm[71]" -type "matrix" 0.031296508417215763 0.99696735386587154 0.071250430781666735 0
		 0.99950952055517228 -0.031296508415754654 -0.0011166380578132027 0 0.0011166380168606271 0.071250430782308583 -0.99745783331069926 0
		 -0.85619999999949958 10.785773530275037 -0.0061267462605225226 1;
	setAttr ".wm[72]" -type "matrix" 2.1596777775578094e-16 0.91948226825734669 0.39313147719347669 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -5.3425822801165998e-17 -0.39313147719347669 0.91948226825734669 0
		 1.4652075732666592e-15 18.666608193938995 0.040971763688547297 1;
	setAttr ".wm[73]" -type "matrix" 9.9799074638824727e-17 0.29900601969327567 0.95425122488115521 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -1.9883798498271469e-16 -0.95425122488115521 0.29900601969327567 0
		 1.5048813522446862e-15 18.835519207721379 0.1131909229425592 1;
	setAttr ".wm[74]" -type "matrix" 1.4699492569040184e-17 -0.095260262111725835 0.99545240090242681 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -2.2199172166764399e-16 -0.99545240090242681 -0.095260262111725835 0
		 1.5252182875665705e-15 18.896450294561244 0.30764708910913174 1;
	setAttr ".wm[75]" -type "matrix" 1.4699492569040184e-17 -0.095260262111725835 0.99545240090242681 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -2.2199172166764399e-16 -0.99545240090242681 -0.095260262111725835 0
		 1.5287251996598398e-15 18.873723702902474 0.54513583551331879 1;
	setAttr ".wm[76]" -type "matrix" 0.23968251738811949 -0.9662825719781567 -0.094075937145330524 0
		 0.36536620039523604 -7.7715611723760958e-16 0.93086386738810944 0 -0.89947753194131641 -0.25748396278463315 0.35304699183179505 0
		 0.62273925060932411 20.600187555848802 -0.35336248589217845 1;
	setAttr ".wm[77]" -type "matrix" 0.23968251738811949 -0.9662825719781567 -0.094075937145330524 0
		 0.36536620039523604 -7.7715611723760958e-16 0.93086386738810944 0 -0.89947753194131641 -0.25748396278463315 0.35304699183179505 0
		 0.72087300000000087 20.150484688992918 -0.43818359398640161 1;
	setAttr ".wm[78]" -type "matrix" -0.26587738998416921 -0.13756804929513772 -0.95414057942649955 0
		 0.036927327179538838 -0.99049231789708025 0.13251920877459508 0 -0.96329932316107292 -5.2735593669694936e-16 0.26842953264761804 0
		 0.79422140942326691 19.635435466440544 -0.44594321714765184 1;
	setAttr ".wm[79]" -type "matrix" -0.26587738998416921 -0.13756804929513772 -0.95414057942649955 0
		 0.036927327179538838 -0.99049231789708025 0.13251920877459508 0 -0.96329932316107292 -5.2735593669694936e-16 0.26842953264761804 0
		 0.82905011907515047 19.12086393603477 -0.42458190930027057 1;
	setAttr ".wm[80]" -type "matrix" -0.036696171561762053 -0.63969093192274151 -0.76775575713147481 0
		 0.030540233855146981 -0.76863223430702843 0.63896148749377546 0 -0.99885969240368422 -3.9551695252271202e-16 0.047742170993968491 0
		 0.87711592420753681 18.645830244660448 -0.27090783678507424 1;
	setAttr ".wm[81]" -type "matrix" -0.036696171561762053 -0.63969093192274151 -0.76775575713147481 0
		 0.030540233855146981 -0.76863223430702843 0.63896148749377546 0 -0.99885969240368422 -3.9551695252271202e-16 0.047742170993968491 0
		 0.90228537234971595 18.238614142722511 0.078770246100692554 1;
	setAttr ".wm[82]" -type "matrix" -0.03592988425822851 -0.64563704750790196 -0.7627986931703995 0
		 0.030377573290232805 -0.76364442176007497 0.6449220109096272 0 -0.9988925099620013 8.9278953153970608e-14 0.047050542417841998 0
		 0.91741473653280947 17.917391778431188 0.40275769351676416 1;
	setAttr ".wm[83]" -type "matrix" -0.03592988425822851 -0.64563704750790196 -0.7627986931703995 0
		 0.030377573290232805 -0.76364442176007497 0.6449220109096272 0 -0.9988925099620013 8.9278953153970608e-14 0.047050542417841998 0
		 0.92533341818831838 17.582822134569977 0.75256099971624513 1;
	setAttr ".wm[84]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.92033137616298888 17.195546679241605 1.0309350431440394 1;
	setAttr ".wm[85]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.92029117294536245 16.867797181855011 1.172442944508391 1;
	setAttr ".wm[86]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.91044090865711846 16.564111681666351 1.2732252106910604 1;
	setAttr ".wm[87]" -type "matrix" 0.99931697839818001 0.036786429205217526 -0.0035121662063185566 0
		 -0.035168339383108337 0.9175463216165527 -0.39607061945184507 0 -0.011347448619218256 0.39592361171602708 0.91821333528519966 0
		 0.88565945787360523 16.093144336919988 1.438688997225356 1;
	setAttr ".wm[88]" -type "matrix" 0.23968251738811952 0.96628257197815659 0.094075937145330191 0
		 0.36536620039523604 4.8572257327350599e-16 -0.93086386738810944 0 -0.89947753194131641 0.25748396278463309 -0.35304699183179505 0
		 -0.62273900000000004 20.600200000000001 -0.35336199999999562 1;
	setAttr ".wm[89]" -type "matrix" 0.23968251738811952 0.96628257197815659 0.094075937145330191 0
		 0.36536620039523604 4.8572257327350599e-16 -0.93086386738810944 0 -0.89947753194131641 0.25748396278463309 -0.35304699183179505 0
		 -0.72087300000000176 20.150500000000001 -0.4381839999999968 1;
	setAttr ".wm[90]" -type "matrix" -0.26587738998416893 0.13756804929513822 0.95414057942649944 0
		 0.036927327179538977 0.99049231789707992 -0.1325192087745955 0 -0.96329932316107292 6.106226635438361e-16 -0.26842953264761793 0
		 -0.79422099999999962 19.635400000000008 -0.44594299999999698 1;
	setAttr ".wm[91]" -type "matrix" -0.26587738998416893 0.13756804929513822 0.95414057942649944 0
		 0.036927327179538977 0.99049231789707992 -0.1325192087745955 0 -0.96329932316107292 6.106226635438361e-16 -0.26842953264761793 0
		 -0.82905000000000073 19.120899999999992 -0.42458199999999768 1;
	setAttr ".wm[92]" -type "matrix" -0.036696171561761748 0.6396909319227414 0.76775575713147481 0
		 0.030540233855147869 0.76863223430702809 -0.63896148749377546 0 -0.998859692403684 1.3253287356462806e-15 -0.047742170993969019 0
		 -0.87711600000000045 18.645800000000001 -0.27090799999999915 1;
	setAttr ".wm[93]" -type "matrix" -0.036696171561761748 0.6396909319227414 0.76775575713147481 0
		 0.030540233855147869 0.76863223430702809 -0.63896148749377546 0 -0.998859692403684 1.3253287356462806e-15 -0.047742170993969019 0
		 -0.90228500000000045 18.238600000000002 0.078770200000001012 1;
	setAttr ".wm[94]" -type "matrix" -0.035929884258228018 0.64563704750790341 0.76279869317039828 0
		 0.030377573290521279 0.76364442176007341 -0.6449220109096151 0 -0.9988925099619923 1.3153421494355166e-13 -0.047050542418028064 0
		 -0.91741500000000031 17.917399999999997 0.402758 1;
	setAttr ".wm[95]" -type "matrix" -0.035929884258228018 0.64563704750790341 0.76279869317039828 0
		 0.030377573290521279 0.76364442176007341 -0.6449220109096151 0 -0.9988925099619923 1.3153421494355166e-13 -0.047050542418028064 0
		 -0.92533300000000007 17.582799999999999 0.75256099999999981 1;
	setAttr ".wm[96]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.92033100000000023 17.195499999999992 1.0309399999999997 1;
	setAttr ".wm[97]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.92029100000000008 16.867799999999995 1.1724399999999993 1;
	setAttr ".wm[98]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.91044100000000017 16.564099999999996 1.2732300000000005 1;
	setAttr ".wm[99]" -type "matrix" 0.99931697839817979 -0.03678642920521661 0.0035121662063207909 0
		 -0.03516833938310835 -0.91754632161655481 0.39607061945183958 0 -0.011347448619215661 -0.39592361171602164 -0.91821333528520233 0
		 -0.8856590000000002 16.093099999999996 1.4386899999999982 1;
	setAttr -s 100 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[3]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 11.290417510307522 -0.30575371918217331 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.13615652300521427 0 0 0.99068733778277929 1
		 1 1 yes;
	setAttr ".xm[4]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0.73294791973833107 -2.7755575615628914e-17 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.061460274103232897 0.061460274103232904 0.70443071675442681 0.70443071675442692 1
		 1 1 yes;
	setAttr ".xm[5]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6059012883365249 -3.3833774298022766e-31
		 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.11368981806260474 0 0.99351629340886594 1
		 1 1 yes;
	setAttr ".xm[6]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.6294198485169147 4.221638438096821e-31
		 -1.1102230246251565e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.013839369459957052 0 0.99990423134065731 1
		 1 1 yes;
	setAttr ".xm[7]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.2179155821930434 -2.0337820212729211e-31
		 2.7755575615628914e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.1007574452602511 0 0.9949110197523332 1
		 1 1 yes;
	setAttr ".xm[8]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.1251701128334721 -1.5264800368591707e-30
		 -8.3266726846886741e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.035296879408558003 0 0.99937687100713801 1
		 1 1 yes;
	setAttr ".xm[9]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.90920262879895186 1.5490976766435683e-30
		 -3.8857805861880479e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.065907826308504211 0 0.99782571545901144 1
		 1 1 yes;
	setAttr ".xm[10]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.0924359929576617 4.1099345013223613e-31
		 -2.2204460492503131e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.034216436942996496 0 0.99941444628488629 1
		 1 1 yes;
	setAttr ".xm[11]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.2750054547438887 2.011838456969059e-30
		 -1.5612511283791264e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[12]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.38813223676744352 -1.0148639098398196e-16
		 0.18495873319083661 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.99614952772992371 0 -0.087670510455055223 1
		 1 1 yes;
	setAttr ".xm[13]" -type "matrix" "xform" 1 1 1 1.4274156856758724e-10 -1.0741296741751788e-11
		 -0.52951544211162549 0 1.1036875395607693 -0.59846639999999973 0.32383580444340093 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20888082964928789 0.055577584331834254 -0.6499651278761428 0.7285775618764363 1
		 1 1 yes;
	setAttr ".xm[14]" -type "matrix" "xform" 1 1 1 -0.057417913726941099 -0.15413224005414905
		 -0.3789828778757085 3 1.4163909364405824 4.3298697960381105e-15 -5.5511151231257857e-16 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619629083776 -0.19151262312050488 -0.035651083353537324 0.98082693497125062 1
		 1 1 yes;
	setAttr ".xm[15]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[16]" -type "matrix" "xform" 1 1 1 0.0028423938112721705 0.033282805334109884
		 -0.085474000382206192 3 2.763029379803347 -2.9901889802249744e-15 6.1977251948291957e-17 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424696022538 6.0215466624456995e-05 0.00028513614521740702 0.99999896722879134 1
		 1 1 yes;
	setAttr ".xm[17]" -type "matrix" "xform" 1 1 1 0 -0.016641402667054942 0 0 1.3262893058653958e-31
		 1.1843548872543966e-16 1.1748840317954808e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0.70710678118654746 0 0.70710678118654757 1 1 1 yes;
	setAttr ".xm[18]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.29999999999999988 2.7829707478258147e-15
		 -3.1086244689504375e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[19]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401444 -0.29225669056177106
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[20]" -type "matrix" "xform" 1 1 1 0 0 0.031415926535897934 3 0.85619999999999941
		 -0.40510070369043732 0.42465902716735693 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071632605204258515 -0.070855182925839061 -0.70358843558290385 0.70342847983160206 1
		 1 1 yes;
	setAttr ".xm[21]" -type "matrix" "xform" 1 1 1 0 0 -0.040142572795869587 3 5.1039432420868449
		 1.1584700213007615e-16 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		-0.00038254971319926455 -0.030667825540422869 5.7912800117392978e-05 0.99952955673078858 1
		 1 1 yes;
	setAttr ".xm[22]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.5943197435413126 1.3242089580900104e-17
		 -4.8572257327350599e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156972832253 -0.48052832367267562 0.0038217968106755776 0.87696843816418957 1
		 1 1 yes;
	setAttr ".xm[23]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[24]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.1282257310760708 1.0961885143939659e-15
		 -4.7610535965885447e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[25]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.2564514621521417 2.1923770287879319e-15
		 -9.5221071931770894e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[26]" -type "matrix" "xform" 1 1 1 0 0 0.15852825595864495 0 3.3846771932282129
		 3.288565543181897e-15 -1.4283160789765633e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0 -0.079181153912334629 0.99686024339679191 1 1 1 yes;
	setAttr ".xm[27]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.10915409999999959 -7.0518867354993834e-16
		 -4.5520648033906218e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349093526172 0.051920268595790221 0.075303689671793003 0.99579767338342862 1
		 1 1 yes;
	setAttr ".xm[28]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.67809966018133316 4.0050428251614534e-16
		 1.5265566588595902e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226642272568 -0.068108891780257405 -0.10891411752763996 0.99169500809891153 1
		 1 1 yes;
	setAttr ".xm[29]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.35468834509693448 -1.5543122344752148e-15
		 6.8782774695160208e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[30]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.44035893053684116 2.2204460492503151e-15
		 -4.1693089501269e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[31]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.62990893714498686 -1.3322676295501873e-15
		 -9.6748875453842723e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[32]" -type "matrix" "xform" 1 1 1 0 0 -0.079264127979322474 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[33]" -type "matrix" "xform" 1 1 1 0 0 0 5 -0.076525269383702535 0.023547569757453157
		 0.19836057277298721 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886703781422 -0.079692662965438754 -0.19114093582264557 0.9230540437946958 1
		 1 1 yes;
	setAttr ".xm[34]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.78036916329648875 1.0269562977782698e-15
		 -1.3877787807814457e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348613168178 0.020782185645402684 0.043527662293890997 0.72745918696323897 1
		 1 1 yes;
	setAttr ".xm[35]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.35245262105826525 4.4408920985006153e-16
		 2.2204460492503348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[36]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.38733069761372629 -8.8817841970012326e-16
		 -3.944304526105059e-30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[37]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.9009795642339747e-16 1.6524790809532086e-18
		 1.8957551425785906e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0023408149950071714 -0.54279005697380478 0.0036618570973429849 0.83985716966525426 1
		 1 1 yes;
	setAttr ".xm[38]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.59601991577807734 1.8175355256292112e-27
		 -8.0491169285323849e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[39]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6633421254816507 5.0487097934144756e-28
		 5.5511151231257827e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491503 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[40]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.89886392169674756 1.1102230246223798e-16
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[41]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[42]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[43]" -type "matrix" "xform" 1 1 1 4.7184478542310744e-16 2.7755575620310616e-16
		 -0.5295154417625596 0 1.1036875399999999 0.59846639999999995 0.32383580439999998 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.64996512791127337 0.72857756184195677 -0.2088808297181233 -0.055577584114279266 1
		 1 1 yes;
	setAttr ".xm[44]" -type "matrix" "xform" 1 1 1 -0.057417913761847683 -0.15413224001924247
		 -0.37898287822477439 3 -1.416390936 4.1969983040000001e-10 2.1459101160000001e-10 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619623608 -0.19151262309887584 -0.035651083397193438 0.98082693497388995 1
		 1 1 yes;
	setAttr ".xm[45]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.3256375430000002e-10 -2.593480986e-11
		 1.3505818690000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[46]" -type "matrix" "xform" 1 1 1 0.0028423938042908535 0.033282805264296708
		 -0.085474000329846311 3 -2.7630293799999999 -6.8785510619999996e-10 5.9058447019999997e-10 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424698124646 6.0215462682850012e-05 0.00028513614109331641 0.99999896722879245 1
		 1 1 yes;
	setAttr ".xm[47]" -type "matrix" "xform" 1 1 1 0 -0.016641402632148354 0 0 -1.359117263e-10
		 8.1712414610000005e-14 -1.6875389970000001e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0.70710678118654746 0 0.70710678118654757 1 1 1 yes;
	setAttr ".xm[48]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.29999999999999999 1.111288839e-10
		 5.1685766779999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[49]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401433 0.29144088923931144
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[50]" -type "matrix" "xform" 1 1 1 0 0 0.031415926535897934 3 -0.85619999999999996
		 -0.40510070370000001 0.42465902719999998 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.7034284798323589 0.70358843558220097 -0.070855182932823474 0.071632605196822852 1
		 1 1 yes;
	setAttr ".xm[51]" -type "matrix" "xform" 1 1 1 0 0 -0.040142572795869587 3 -5.1039432419999997
		 -2.9864999360000001e-14 2.6777802200000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		-0.00038254971320976207 -0.030667825540029232 5.7912799514840228e-05 0.99952955673080068 1
		 1 1 yes;
	setAttr ".xm[52]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.5943197439999999 -1.129296656e-11
		 -2.2188917369999999e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156974160557 -0.48052832367275899 0.0038217968109156681 0.87696843816414249 1
		 1 1 yes;
	setAttr ".xm[53]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.0874435509999999e-10 -3.3715252810000002e-12
		 -3.2691249709999998e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[54]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.1282257309999999 -2.7998581230000002e-10
		 1.9434587269999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[55]" -type "matrix" "xform" 1 1 1 0 0 0 0 -2.2564514619999998 -5.6006399520000001e-10
		 3.8870950899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[56]" -type "matrix" "xform" 1 1 1 0 0 0.15852825595864495 0 -3.3846771929999999
		 -8.4013862530000004e-10 5.8307136899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0 -0.079181153912334629 0.99686024339679191 1 1 1 yes;
	setAttr ".xm[57]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.1091541004 -8.4579454550000004e-11
		 1.21866961e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349092261559 0.051920268596349434 0.075303689673768381 0.99579767338325065 1
		 1 1 yes;
	setAttr ".xm[58]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.6780996601 -1.4295409300000001e-10
		 1.2093082090000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226671807475 -0.068108891780949685 -0.10891411756533778 0.9916950080947049 1
		 1 1 yes;
	setAttr ".xm[59]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.35468834510000002 -1.2705569930000001e-10
		 3.5710101540000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[60]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.44035893059999998 -1.4656365009999999e-10
		 3.7431391319999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[61]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.62990893709999995 -2.0963852879999999e-10
		 5.3545612389999999e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[62]" -type "matrix" "xform" 1 1 1 0 0 -0.079264127979322474 0 -3.5955682879999998e-10
		 -5.7475801900000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[63]" -type "matrix" "xform" 1 1 1 0 0 0 5 0.076525269009999994 -0.02354756987
		 -0.1983605728 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886706096509 -0.07969266291038643 -0.19114093584315128 0.92305404378707212 1
		 1 1 yes;
	setAttr ".xm[64]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.78036916329999995 -2.329372251e-10
		 -2.343245598e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348614366042 0.020782185649366937 0.043527662292334027 0.72745918695194833 1
		 1 1 yes;
	setAttr ".xm[65]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.35245262100000002 -1.1430856259999999e-10
		 9.2377661080000006e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[66]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.3873306977 -1.2523138080000001e-10
		 1.005204808e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[67]" -type "matrix" "xform" 1 1 1 0 0 0 0 -7.0798478190000004e-11 6.5503158450000003e-15
		 4.3484105210000001e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.002340814995055578 -0.5427900569738866 0.0036618570974149794 0.83985716966520096 1
		 1 1 yes;
	setAttr ".xm[68]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.59601991580000002 -1.1653567000000001e-11
		 -6.323830348e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[69]" -type "matrix" "xform" 1 1 1 0 0 0 3 -1.663342125 -3.3700819910000002e-11
		 -3.2867686350000002e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491506 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[70]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.89886392189999997 -1.8376633549999999e-11
		 1.0505785129999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[71]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.5912604569999999e-11 -3.1197266989999997e-14
		 3.0063063150000003e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[72]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.47564845123849153 1.0631297916735791e-16
		 -0.027659795107475748 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.96547823737110805 0 0.26048372917089935 1
		 1 1 yes;
	setAttr ".xm[73]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.18370230684547595 9.8607613152626476e-31
		 6.6613381477509392e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.41828403814789133 0 0.90831627940420256 1
		 1 1 yes;
	setAttr ".xm[74]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.20377879650171854 5.8355677314933246e-31
		 -6.9388939039072284e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19820660803431642 0 0.98016026267724754 1
		 1 1 yes;
	setAttr ".xm[75]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.23857368387367603 -3.9313044989804452e-31
		 3.5492442318485473e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[76]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21644808540609339 -0.62273925060932223
		 -0.20008910385773135 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.08571835649344578 -0.55642581752290021 -0.82178796751819183 0.087790713611145488 1
		 1 1 yes;
	setAttr ".xm[77]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.46604061213981773 -0.043102149571323196
		 -0.0024236635249148164 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[78]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.51599341270102894 0.019575876830657486
		 0.063902156957241218 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122638 -0.064517222783691514 -0.64525574015412179 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[79]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.041146744595169038 0.51379606264634836
		 -0.027816466552018193 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[80]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.094056821136732097 0.49265693025971274
		 -0.0050510980859091257 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912757 0.10223239472282354 0.27275670110683287 0.95556889816367396 1
		 1 1 yes;
	setAttr ".xm[81]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.0088985359227593489 0.53719893109528427
		 -0.0084463564032919228 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[82]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.043815384167760076 0.45437941922514219
		 0.00035575206024950762 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411100415487 0.00026524166420574817 0.0038805462674768852 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[83]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.051103465102685583 0.48132864421422783
		 0.0085485235017488601 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[84]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.037875747802228063 0.47511833912037177
		 0.018094152051907897 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084785637 -0.024433420154250138 -0.17352495576627536 0.98442348766544641 1
		 1 1 yes;
	setAttr ".xm[85]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.018793975249772624 0.35619597747174936
		 0.01467763363979435 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[86]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.011852099687511403 0.31926408905670134
		 0.020222390563214634 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[87]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.010747678320721432 0.49793861709289661
		 0.04176416876903332 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.66815275056484158 0.020937923968194282 -0.74349139430409505 0.018816265524581065 1
		 1 1 yes;
	setAttr ".xm[88]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21643563291215034 0.62273900000000193
		 -0.20008927233585919 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.82178796751819183 0.087790713611145405 -0.08571835649344553 0.55642581752290021 1
		 1 1 yes;
	setAttr ".xm[89]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.46603798592048273 0.043102888250008409
		 0.0024249419964386121 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[90]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.51604232130763428 -0.019576307319524755
		 -0.063915819607909596 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122641 -0.064517222783691486 -0.6452557401541219 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[91]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.04113712082946322 -0.51372518225503505
		 0.027816828879492217 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[92]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.094047681809646982 -0.49272260603033041
		 0.0050513052669699521 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912292 0.10223239472282343 0.2727567011068327 0.95556889816367407 1
		 1 1 yes;
	setAttr ".xm[93]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.0089089096564693923 -0.53718661577186799
		 0.0084459031808444829 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[94]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.043829984432502161 -0.45436247401548463
		 -0.00035513380149254647 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411086023657 0.0002652416642052489 0.0038805462674778783 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[95]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.051083607994496634 -0.48135160732845123
		 -0.0085491899956186002 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[96]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.037887812374790837 -0.47514028040108791
		 -0.018094343282668901 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084644157 -0.02443342015422496 -0.17352495576627963 0.98442348766544829 1
		 1 1 yes;
	setAttr ".xm[97]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.018803727656725167 -0.35614682144038068
		 -0.014676614191331594 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[98]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.011849867191743121 -0.31928036338535581
		 -0.020222927682530312 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[99]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.010762552102557693 -0.49796793861719396
		 -0.04176432335838054 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.66815275056484258 -0.020937923968192444 0.74349139430409417 -0.01881626552457839 1
		 1 1 yes;
	setAttr -s 97 ".m";
	setAttr -s 100 ".p";
	setAttr -s 100 ".g[0:99]" yes yes yes no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no;
	setAttr -l on ".amt" 109051904;
createNode dagPose -n "FBX_AMTStance";
	addAttr -ci true -h true -sn "amt" -ln "AMobjectTypeID" -at "long";
	setAttr -s 100 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[2]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[3]" -type "matrix" 1 0 0 0 0 0.96292280248626105 0.26977708659559096 0
		 0 -0.26977708659559096 0.96292280248626105 0 0 11.290417510307522 -0.30575371918217331 1
		;
	setAttr ".wm[4]" -type "matrix" 2.2204460492503131e-16 0.99509301942264905 0.098943836070343738 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.3877787807814454e-17 -0.098943836070343738 0.99509301942264905 0
		 0 11.996189775258431 -0.10802116476886733 1;
	setAttr ".wm[5]" -type "matrix" 2.1316951863865569e-16 0.99172106330715759 -0.128410796247513 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.3680105952454152e-17 0.128410796247513 0.99172106330715759 0
		 3.565817171172828e-16 13.594210937163945 0.05087286904945576 1;
	setAttr ".wm[6]" -type "matrix" 2.113254464861858e-16 0.98778726979368714 -0.15580856726615877 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 6.9555411278822762e-17 0.15580856726615877 0.98778726979368714 0
		 7.0392436188590434e-16 15.210140921908927 -0.15836223112010339 1;
	setAttr ".wm[7]" -type "matrix" 2.209797897348894e-16 0.99896907691404224 0.045395851897569228 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.5774640627485565e-17 -0.045395851897569228 0.99896907691404224 0
		 9.6130091607533248e-16 16.413182429682582 -0.34812391303273083 1;
	setAttr ".wm[8]" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr ".wm[9]" -type "matrix" 2.1898562510217626e-16 0.99987373456677664 -0.01589071815515776 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 3.9264431351556042e-17 0.01589071815515776 0.99987373456677664 0
		 1.4120088374132143e-15 18.440282855871136 -0.19179676487531067 1;
	setAttr ".wm[10]" -type "matrix" 2.2115826839442644e-16 0.99861931185935604 0.052530657539630252 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr ".wm[11]" -type "matrix" 2.2115826839442644e-16 0.99861931185935604 0.052530657539630252 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 1.9332146147797686e-15 20.805825981758147 -0.14217948243763939 1;
	setAttr ".wm[12]" -type "matrix" -2.1353245134360761e-16 -0.99244361258999347 0.1227015722365561 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -6.2452316161546887e-17 -0.1227015722365561 -0.99244361258999347 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[13]" -type "matrix" 0.92388183249513889 0.16476216079436845 -0.34539222625269761 0
		 -0.067828263099948841 0.95878037427535223 0.27593390626970704 0 0.37661875459178629 -0.23150296817705382 0.89697530033716399 0
		 0.59846640000000095 17.501031350061492 0.025480877690902903 1;
	setAttr ".wm[14]" -type "matrix" 0.99999982742939508 0.00016861565242734522 -0.00056276988345721479 0
		 -2.0827193368863628e-05 0.96749988670756215 0.25287144715661802 0 0.00058711788252985286 -0.25287139179752222 0.96749972325731226 0
		 1.9070442538882317 17.734398981279003 -0.46372954109045228 1;
	setAttr ".wm[15]" -type "matrix" 0.99999982742939508 0.00016861565242734522 -0.00056276988345721479 0
		 -2.0827193368863628e-05 0.96749988670756215 0.25287144715661802 0 0.00058711788252985286 -0.25287139179752222 0.96749972325731226 0
		 1.9070442538882317 17.734398981279003 -0.46372954109045228 1;
	setAttr ".wm[16]" -type "matrix" 0.99999957452046417 0.0007508459039998795 -0.00053590047498160056 0
		 -0.00059292072807430661 0.96820754459588965 0.25014755452054399 0 0.00070668514973705248 -0.25014713034137875 0.96820757783549294 0
		 4.6700731568739275 17.73486487128055 -0.46528449081251377 1;
	setAttr ".wm[17]" -type "matrix" -0.00070668514973683044 0.25014713034137875 -0.96820757783549294 0
		 -0.00059292072807430661 0.96820754459588965 0.25014755452054399 0 0.99999957452046417 0.00075084590399982398 -0.00053590047498138556 0
		 4.6700731568739275 17.73486487128055 -0.46528449081251361 1;
	setAttr ".wm[18]" -type "matrix" -0.00070668514973683044 0.25014713034137875 -0.96820757783549294 0
		 -0.00059292072807430661 0.96820754459588965 0.25014755452054399 0 0.99999957452046417 0.00075084590399982398 -0.00053590047498138556 0
		 4.6698611513290036 17.809909010382967 -0.75574676416316067 1;
	setAttr ".wm[19]" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 0.29225669056177278 19.851563453626383 0.41745445901943362 1;
	setAttr ".wm[20]" -type "matrix" -0.00011428726690443369 -0.9974584577452823 -0.071250347443529732 0
		 0.99999937002875883 -3.4435881491260334e-05 -0.001121943071602629 0 0.0011166380373579395 -0.071250430781667123 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr ".wm[21]" -type "matrix" 9.3620121673563885e-05 -0.99995033799989919 -0.0099655792185021422 0
		 0.99999822327849597 0.00011237780952950964 -0.001881704301883432 0 0.0018827307626474124 -0.0099653853470574941 0.99994857188745456 0
		 0.85561668427642601 5.694802175603642 -0.36978447559126582 1;
	setAttr ".wm[22]" -type "matrix" 0.0063515645323270649 -0.54652773965413159 0.83741691373923044 0
		 0.99995955077848053 0.0088043898604805819 -0.0018383487385393697 0 -0.0063682364035508535 0.83739471726762804 0.54656155468289036 0
		 0.85604680504982367 1.1007105951698968 -0.41556953295065524 1;
	setAttr ".wm[23]" -type "matrix" 0.0063515645323270649 -0.54652773965413159 0.83741691373923044 0
		 0.99995955077848053 0.0088043898604805819 -0.0018383487385393697 0 -0.0063682364035508535 0.83739471726762804 0.54656155468289036 0
		 0.85604680504982367 1.1007105951698968 -0.41556953295065524 1;
	setAttr ".wm[24]" -type "matrix" 0.99999957452046417 0.0007508459039998795 -0.00053590047498160056 0
		 -0.00059292072807430661 0.96820754459588965 0.25014755452054399 0 0.00070668514973705248 -0.25014713034137875 0.96820757783549294 0
		 5.7982984079130375 17.735711994949515 -0.4658891075176837 1;
	setAttr ".wm[25]" -type "matrix" 0.99999957452046417 0.0007508459039998795 -0.00053590047498160056 0
		 -0.00059292072807430661 0.96820754459588965 0.25014755452054399 0 0.00070668514973705248 -0.25014713034137875 0.96820757783549294 0
		 6.9265236589521484 17.736559118618484 -0.46649372422285357 1;
	setAttr ".wm[26]" -type "matrix" 0.98755387106924963 -0.15210473911564146 -0.040018746540873604 0
		 0.15727953564351319 0.95618542214391455 0.2469262767451551 0 0.00070668514973705248 -0.25014713034137875 0.96820757783549294 0
		 8.0547489099912593 17.737406242287452 -0.46709834092802349 1;
	setAttr ".wm[27]" -type "matrix" 0.99461892125055462 0.019989941936517236 -0.10165433444648403 0
		 0.0078591531488033661 0.96382261959958326 0.26642858641666267 0 0.10330263889255985 -0.26579383019470582 0.9584791101679061 0
		 8.1625444639893381 17.720803386383551 -0.47146655118982089 1;
	setAttr ".wm[28]" -type "matrix" 0.97420027006291154 -0.2243154717341779 -0.024827463624450402 0
		 0.2236229994098303 0.94460166693911396 0.24025079594207041 0 -0.030439907100731162 -0.23960438217303251 0.97039329763718885 0
		 8.8369952164992629 17.734358559217746 -0.54039832083394101 1;
	setAttr ".wm[29]" -type "matrix" 0.97420027006291154 -0.2243154717341779 -0.024827463624450402 0
		 0.2236229994098303 0.94460166693911396 0.24025079594207041 0 -0.030439907100731162 -0.23960438217303251 0.97039329763718885 0
		 9.1825326980808626 17.654796475768713 -0.54920433281985193 1;
	setAttr ".wm[30]" -type "matrix" 0.97420027006291154 -0.2243154717341779 -0.024827463624450402 0
		 0.2236229994098303 0.94460166693911396 0.24025079594207041 0 -0.030439907100731162 -0.23960438217303251 0.97039329763718885 0
		 9.611530487134468 17.556017154532988 -0.56013732814945671 1;
	setAttr ".wm[31]" -type "matrix" 0.97420027006291154 -0.2243154717341779 -0.024827463624450402 0
		 0.2236229994098303 0.94460166693911396 0.24025079594207041 0 -0.030439907100731162 -0.23960438217303251 0.97039329763718885 0
		 10.225187943816156 17.414718834147735 -0.57577636937314047 1;
	setAttr ".wm[32]" -type "matrix" 0.98755387106924963 -0.15210473911564146 -0.040018746540873604 0
		 0.15727953564351319 0.95618542214391455 0.2469262767451551 0 0.00070668514973705248 -0.25014713034137875 0.96820757783549294 0
		 8.0547489099912593 17.737406242287452 -0.46709834092802349 1;
	setAttr ".wm[33]" -type "matrix" 0.85566893335035843 -0.49486180267263086 0.15146772842640199 0
		 0.5118298932359262 0.76590323374657499 -0.38913030841434038 0 0.076556102886447985 0.41049242720436846 0.90864466669799238 0
		 7.983019813284824 17.72194261329977 -0.26616717213938534 1;
	setAttr ".wm[34]" -type "matrix" 0.90090901117274447 -0.41021851439160717 0.14171705627090503 0
		 0.076858681077952157 0.47216732923763571 0.87815189821781714 0 -0.42714833106393574 -0.78024277225165062 0.45690865566144967 0
		 8.6507574628622432 17.335767722400739 -0.14796642764085477 1;
	setAttr ".wm[35]" -type "matrix" 0.90090901117274447 -0.41021851439160717 0.14171705627090503 0
		 0.076858681077952157 0.47216732923763571 0.87815189821781714 0 -0.42714833106393574 -0.78024277225165062 0.45690865566144967 0
		 8.9682852051850865 17.191185131796789 -0.098017879709512132 1;
	setAttr ".wm[36]" -type "matrix" 0.90090901117274447 -0.41021851439160717 0.14171705627090503 0
		 0.076858681077952157 0.47216732923763571 0.87815189821781714 0 -0.42714833106393574 -0.78024277225165062 0.45690865566144967 0
		 9.3172349209691188 17.032294908443422 -0.043126513440339562 1;
	setAttr ".wm[37]" -type "matrix" 0.0053647565628082905 -0.41979622029029179 0.90760253019535286 0
		 0.99995955077836352 0.0088043898724669226 -0.0018383487447948929 0 -0.0072191546704372077 0.90757568067294447 0.41982647326828482 0
		 0.85561668427642601 5.694802175603642 -0.36978447559126582 1;
	setAttr ".wm[38]" -type "matrix" 0.0053647565628082905 -0.41979622029029179 0.90760253019535286 0
		 0.99995955077836352 0.0088043898724669226 -0.0018383487447948929 0 -0.0072191546704372077 0.90757568067294447 0.41982647326828482 0
		 0.85881418603116089 5.4445952677422662 0.17116470801573791 1;
	setAttr ".wm[39]" -type "matrix" 0.0033789990585033846 -0.17831876663506391 0.98396697090456875 0
		 0.99995955077848053 0.0088043898604805819 -0.0018383487385393697 0 -0.008335416741978692 0.98393338198525127 0.17834130380482049 0
		 0.86661162989915841 0.19164798305891129 0.97734129626264044 1;
	setAttr ".wm[40]" -type "matrix" 0.0033789990585033846 -0.17831876663506391 0.98396697090456875 0
		 0.99995955077848053 0.0088043898604805819 -0.0018383487385393697 0 -0.008335416741978692 0.98393338198525127 0.17834130380482049 0
		 0.86964889024429448 0.031363677169190612 1.8617937065499905 1;
	setAttr ".wm[41]" -type "matrix" -0.00011428726690443369 -0.9974584577452823 -0.071250347443529732 0
		 0.99999937002875883 -3.4435881491260334e-05 -0.001121943071602629 0 0.0011166380373579395 -0.071250430781667123 0.99745783331072213 0
		 0.85619999999999941 10.785773530275042 -0.0061267462605226752 1;
	setAttr ".wm[42]" -type "matrix" 2.2224756065090724e-16 0.99327723941252521 0.11575977567805114 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 1.0120343644030153e-17 -0.11575977567805114 0.99327723941252521 0
		 1.2099407710252564e-15 17.537192578671103 -0.29704585723097132 1;
	setAttr ".wm[43]" -type "matrix" 0.92388183258474355 -0.16476216074160643 0.34539222603818509 0
		 -0.067828262951100768 -0.95878037418200612 -0.27593390663064266 0 0.37661875439878473 0.23150296860120162 -0.8969753003087314 0
		 -0.59846639999999873 17.501031350502242 0.025480877667486079 1;
	setAttr ".wm[44]" -type "matrix" 0.99999982742949678 -0.00016861537896081802 0.00056276978452968196 0
		 -2.0826953588071184e-05 -0.96749988661380992 -0.25287144751533819 0 0.00058711771767344656 0.25287139215640514 -0.96749972316361266 0
		 -1.9070442535557475 17.734398981219705 -0.46372954096615471 1;
	setAttr ".wm[45]" -type "matrix" 0.99999982742949678 -0.00016861537896081802 0.00056276978452968196 0
		 -2.0826953588071184e-05 -0.96749988661380992 -0.25287144751533819 0 0.00058711771767344656 0.25287139215640514 -0.96749972316361266 0
		 -1.9070442538882313 17.734398981279007 -0.46372954109045245 1;
	setAttr ".wm[46]" -type "matrix" 0.99999957452073296 -0.00075084562055772151 0.0005359003702830351 0
		 -0.00059292047957155709 -0.96820754450341573 -0.25014755487905677 0 0.00070668497768450254 0.25014713070015399 -0.9682075777429251 0
		 -4.6700731567380158 17.734864871280536 -0.46528449081243789 1;
	setAttr ".wm[47]" -type "matrix" -0.0007066849776842805 -0.25014713070015399 0.9682075777429251 0
		 -0.00059292047957155709 -0.96820754450341573 -0.25014755487905677 0 0.99999957452073296 -0.000750845620557666 0.0005359003702828201 0
		 -4.6700731568739275 17.734864871280557 -0.46528449081251483 1;
	setAttr ".wm[48]" -type "matrix" -0.0007066849776842805 -0.25014713070015399 0.9682075777429251 0
		 -0.00059292047957155709 -0.96820754450341573 -0.25014755487905677 0 0.99999957452073296 -0.000750845620557666 0.0005359003702828201 0
		 -4.6698611513290027 17.809909010382967 -0.75574676416316322 1;
	setAttr ".wm[49]" -type "matrix" 1 4.1823081577675608e-18 -3.4875159182894283e-17 0
		 -8.8633653060486911e-19 0.99861931185935604 0.052530657539630252 0 2.4195451876970254e-17 -0.052530657539630252 0.99861931185935604 0
		 -0.29144088923930972 19.851563453626383 0.41745445901943362 1;
	setAttr ".wm[50]" -type "matrix" -0.00011428726690554392 0.99745845774523645 0.071250347444171858 0
		 0.9999993700287817 3.443588295190303e-05 0.0011219430511574399 0 0.0011166380168606271 0.071250430782308638 -0.99745783331069937 0
		 -0.85619999999999996 10.785773530257028 -0.0061267462316696997 1;
	setAttr ".wm[51]" -type "matrix" 9.3620119210758657e-05 0.99995033799988542 0.0099655792199274604 0
		 0.99999822327853449 -0.00011237780686639771 0.0018817042815080518 0 0.0018827307422467096 0.0099653853484897997 -0.99994857188747888 0
		 -0.85561668427643067 5.6948021756743943 -0.36978447558621236 1;
	setAttr ".wm[52]" -type "matrix" 0.0063515645141004242 0.54652773965518098 -0.83741691373868377 0
		 0.9999595507785366 -0.0088043898583662177 0.0018383487181454904 0 -0.0063682364129191305 -0.83739471726696546 -0.54656155468379641 0
		 -0.85604680504985342 1.1007105947820257 -0.4155695329545237 1;
	setAttr ".wm[53]" -type "matrix" 0.0063515645141004242 0.54652773965518098 -0.83741691373868377 0
		 0.9999595507785366 -0.0088043898583662177 0.0018383487181454904 0 -0.0063682364129191305 -0.83739471726696546 -0.54656155468379641 0
		 -0.85604680504981712 1.1007105951698948 -0.41556953295065813 1;
	setAttr ".wm[54]" -type "matrix" 0.99999957452073296 -0.00075084562055772151 0.0005359003702830351 0
		 -0.00059292047957155709 -0.96820754450341573 -0.25014755487905677 0 0.00070668497768450254 0.25014713070015399 -0.9682075777429251 0
		 -5.7982984077010551 17.735711994949355 -0.46588910751757301 1;
	setAttr ".wm[55]" -type "matrix" 0.99999957452073296 -0.00075084562055772151 0.0005359003702830351 0
		 -0.00059292047957155709 -0.96820754450341573 -0.25014755487905677 0 0.00070668497768450254 0.25014713070015399 -0.9682075777429251 0
		 -6.9265236586640953 17.736559118618271 -0.46649372422270224 1;
	setAttr ".wm[56]" -type "matrix" 0.98755387103028502 0.15210473938093103 0.040018746494084538 0
		 0.15727953588894233 -0.9561854220078545 -0.24692627711570064 0 0.00070668497768450254 0.25014713070015399 -0.9682075777429251 0
		 -8.0547489096271345 17.737406242287182 -0.46709834092783065 1;
	setAttr ".wm[57]" -type "matrix" 0.99461892126674945 -0.019989941696161279 0.10165433433529235 0
		 0.0078591533904023847 -0.96382261949870196 -0.26642858677447923 0 0.10330263871825093 0.2657938305785974 -0.95847911008023667 0
		 -8.1625444640292777 17.720803386377401 -0.47146655119144248 1;
	setAttr ".wm[58]" -type "matrix" 0.97420026998590181 0.22431547206891048 0.024827463621917623 0
		 0.22362299972246982 -0.94460166677334156 -0.24025079630284019 0 -0.030439907268585198 0.23960438251318861 -0.97039329754793424 0
		 -8.83699521645792 17.734358559216911 -0.54039832082971861 1;
	setAttr ".wm[59]" -type "matrix" 0.97420026998590181 0.22431547206891048 0.024827463621917623 0
		 0.22362299972246982 -0.94460166677334156 -0.24025079630284019 0 -0.030439907268585198 0.23960438251318861 -0.97039329754793424 0
		 -9.1825326980446924 17.654796475777037 -0.54920433281893466 1;
	setAttr ".wm[60]" -type "matrix" 0.97420026998590181 0.22431547206891048 0.024827463621917623 0
		 0.22362299972246982 -0.94460166677334156 -0.24025079630284019 0 -0.030439907268585198 0.23960438251318861 -0.97039329754793424 0
		 -9.6115304871598291 17.556017154527151 -0.56013732815010386 1;
	setAttr ".wm[61]" -type "matrix" 0.97420026998590181 0.22431547206891048 0.024827463621917623 0
		 0.22362299972246982 -0.94460166677334156 -0.24025079630284019 0 -0.030439907268585198 0.23960438251318861 -0.97039329754793424 0
		 -10.225187943797691 17.414718834151991 -0.57577636937266941 1;
	setAttr ".wm[62]" -type "matrix" 0.98755387103028502 0.15210473938093103 0.040018746494084538 0
		 0.15727953588894233 -0.9561854220078545 -0.24692627711570064 0 0.00070668497768450254 0.25014713070015399 -0.9682075777429251 0
		 -8.0547489099912557 17.737406242287449 -0.46709834092802738 1;
	setAttr ".wm[63]" -type "matrix" 0.85566893318544068 0.49486180301553706 -0.15146772823773763 0
		 0.5118298934894765 -0.76590323371527258 0.38913030814245164 0 0.076556103034575926 -0.41049242684938758 -0.90864466684587952 0
		 -7.9830198132821035 17.72194261328945 -0.26616717211341978 1;
	setAttr ".wm[64]" -type "matrix" 0.90090901103704268 0.41021851474675197 -0.14171705610555854 0
		 0.076858681237881074 -0.47216732886507584 -0.87815189840413865 0 -0.4271483313213702 0.78024277229038619 -0.45690865535463537 0
		 -8.6507574628709918 17.335767722395683 -0.14796642763930987 1;
	setAttr ".wm[65]" -type "matrix" 0.90090901103704268 0.41021851474675197 -0.14171705610555854 0
		 0.076858681237881074 -0.47216732886507584 -0.87815189840413865 0 -0.4271483313213702 0.78024277229038619 -0.45690865535463537 0
		 -8.9682852051417594 17.191185131816514 -0.098017879716329581 1;
	setAttr ".wm[66]" -type "matrix" 0.90090901103704268 0.41021851474675197 -0.14171705610555854 0
		 0.076858681237881074 -0.47216732886507584 -0.87815189840413865 0 -0.4271483313213702 0.78024277229038619 -0.45690865535463537 0
		 -9.3172349210035161 17.032294908427758 -0.043126513434930049 1;
	setAttr ".wm[67]" -type "matrix" 0.0053647565432642921 0.41979622029142388 -0.90760253019494497 0
		 0.9999595507784228 -0.0088043898699772909 0.0018383487244038579 0 -0.0072191546767318175 -0.9075756806724451 -0.41982647326925626 0
		 -0.85561668427642257 5.6948021756036429 -0.36978447559126609 1;
	setAttr ".wm[68]" -type "matrix" 0.0053647565432642921 0.41979622029142388 -0.90760253019494497 0
		 0.9999595507784228 -0.0088043898699772909 0.0018383487244038579 0 -0.0072191546767318175 -0.9075756806724451 -0.41982647326925626 0
		 -0.85881418603127502 5.4445952677330673 0.17116470803563605 1;
	setAttr ".wm[69]" -type "matrix" 0.0033789990380689713 0.17831876663628815 -0.98396697090441709 0
		 0.9999595507785366 -0.0088043898583662177 0.0018383487181454904 0 -0.0083354167435310544 -0.98393338198504843 -0.17834130380586771 0
		 -0.86661162989741813 0.19164798320805909 0.97734129603410036 1;
	setAttr ".wm[70]" -type "matrix" 0.0033789990380689713 0.17831876663628815 -0.98396697090441709 0
		 0.9999595507785366 -0.0088043898583662177 0.0018383487181454904 0 -0.0083354167435310544 -0.98393338198504843 -0.17834130380586771 0
		 -0.86964889024412473 0.031363677177786126 1.8617937065025378 1;
	setAttr ".wm[71]" -type "matrix" -0.00011428726690554392 0.99745845774523645 0.071250347444171858 0
		 0.9999993700287817 3.443588295190303e-05 0.0011219430511574399 0 0.0011166380168606271 0.071250430782308638 -0.99745783331069937 0
		 -0.85619999999999941 10.785773530275042 -0.0061267462605225937 1;
	setAttr ".wm[72]" -type "matrix" 2.1596777775578094e-16 0.91948226825734669 0.39313147719347669 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -5.3425822801165998e-17 -0.39313147719347669 0.91948226825734669 0
		 1.4652075732666592e-15 18.666608193938995 0.040971763688547297 1;
	setAttr ".wm[73]" -type "matrix" 9.9799074638824727e-17 0.29900601969327567 0.95425122488115521 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -1.9883798498271469e-16 -0.95425122488115521 0.29900601969327567 0
		 1.5048813522446862e-15 18.835519207721379 0.1131909229425592 1;
	setAttr ".wm[74]" -type "matrix" 1.4699492569040184e-17 -0.095260262111725835 0.99545240090242681 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -2.2199172166764399e-16 -0.99545240090242681 -0.095260262111725835 0
		 1.5252182875665705e-15 18.896450294561244 0.30764708910913174 1;
	setAttr ".wm[75]" -type "matrix" 1.4699492569040184e-17 -0.095260262111725835 0.99545240090242681 0
		 -1 2.1755572241454978e-16 4.6539308282733596e-17 0 -2.2199172166764399e-16 -0.99545240090242681 -0.095260262111725835 0
		 1.5287251996598398e-15 18.873723702902474 0.54513583551331879 1;
	setAttr ".wm[76]" -type "matrix" 0.23968251738811949 -0.9662825719781567 -0.094075937145330524 0
		 0.36536620039523604 -7.7715611723760958e-16 0.93086386738810944 0 -0.89947753194131641 -0.25748396278463315 0.35304699183179505 0
		 0.62273925060932411 20.600187555848802 -0.35336248589217845 1;
	setAttr ".wm[77]" -type "matrix" 0.23968251738811949 -0.9662825719781567 -0.094075937145330524 0
		 0.36536620039523604 -7.7715611723760958e-16 0.93086386738810944 0 -0.89947753194131641 -0.25748396278463315 0.35304699183179505 0
		 0.72087300000000087 20.150484688992918 -0.43818359398640161 1;
	setAttr ".wm[78]" -type "matrix" -0.26587738998416921 -0.13756804929513772 -0.95414057942649955 0
		 0.036927327179538838 -0.99049231789708025 0.13251920877459508 0 -0.96329932316107292 -5.2735593669694936e-16 0.26842953264761804 0
		 0.79422140942326691 19.635435466440544 -0.44594321714765184 1;
	setAttr ".wm[79]" -type "matrix" -0.26587738998416921 -0.13756804929513772 -0.95414057942649955 0
		 0.036927327179538838 -0.99049231789708025 0.13251920877459508 0 -0.96329932316107292 -5.2735593669694936e-16 0.26842953264761804 0
		 0.82905011907515047 19.12086393603477 -0.42458190930027057 1;
	setAttr ".wm[80]" -type "matrix" -0.036696171561762053 -0.63969093192274151 -0.76775575713147481 0
		 0.030540233855146981 -0.76863223430702843 0.63896148749377546 0 -0.99885969240368422 -3.9551695252271202e-16 0.047742170993968491 0
		 0.87711592420753681 18.645830244660448 -0.27090783678507424 1;
	setAttr ".wm[81]" -type "matrix" -0.036696171561762053 -0.63969093192274151 -0.76775575713147481 0
		 0.030540233855146981 -0.76863223430702843 0.63896148749377546 0 -0.99885969240368422 -3.9551695252271202e-16 0.047742170993968491 0
		 0.90228537234971595 18.238614142722511 0.078770246100692554 1;
	setAttr ".wm[82]" -type "matrix" -0.03592988425822851 -0.64563704750790196 -0.7627986931703995 0
		 0.030377573290232805 -0.76364442176007497 0.6449220109096272 0 -0.9988925099620013 8.9278953153970608e-14 0.047050542417841998 0
		 0.91741473653280947 17.917391778431188 0.40275769351676416 1;
	setAttr ".wm[83]" -type "matrix" -0.03592988425822851 -0.64563704750790196 -0.7627986931703995 0
		 0.030377573290232805 -0.76364442176007497 0.6449220109096272 0 -0.9988925099620013 8.9278953153970608e-14 0.047050542417841998 0
		 0.92533341818831838 17.582822134569977 0.75256099971624513 1;
	setAttr ".wm[84]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.92033137616298888 17.195546679241605 1.0309350431440394 1;
	setAttr ".wm[85]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.92029117294536245 16.867797181855011 1.172442944508391 1;
	setAttr ".wm[86]" -type "matrix" -0.097065876695656417 -0.34562115118083298 -0.93334036419611643 0
		 0.035751219841573582 -0.93837413639573208 0.34376711655334868 0 -0.99463564477709276 -1.0130785099704553e-15 0.10344048597554475 0
		 0.91044090865711846 16.564111681666351 1.2732252106910604 1;
	setAttr ".wm[87]" -type "matrix" 0.99931697839818001 0.036786429205217526 -0.0035121662063185566 0
		 -0.035168339383108337 0.9175463216165527 -0.39607061945184507 0 -0.011347448619218256 0.39592361171602708 0.91821333528519966 0
		 0.88565945787360523 16.093144336919988 1.438688997225356 1;
	setAttr ".wm[88]" -type "matrix" 0.23968251738811952 0.96628257197815659 0.094075937145330191 0
		 0.36536620039523604 4.8572257327350599e-16 -0.93086386738810944 0 -0.89947753194131641 0.25748396278463309 -0.35304699183179505 0
		 -0.62273900000000004 20.600200000000001 -0.35336199999999562 1;
	setAttr ".wm[89]" -type "matrix" 0.23968251738811952 0.96628257197815659 0.094075937145330191 0
		 0.36536620039523604 4.8572257327350599e-16 -0.93086386738810944 0 -0.89947753194131641 0.25748396278463309 -0.35304699183179505 0
		 -0.72087300000000176 20.150500000000001 -0.4381839999999968 1;
	setAttr ".wm[90]" -type "matrix" -0.26587738998416893 0.13756804929513822 0.95414057942649944 0
		 0.036927327179538977 0.99049231789707992 -0.1325192087745955 0 -0.96329932316107292 6.106226635438361e-16 -0.26842953264761793 0
		 -0.79422099999999962 19.635400000000008 -0.44594299999999698 1;
	setAttr ".wm[91]" -type "matrix" -0.26587738998416893 0.13756804929513822 0.95414057942649944 0
		 0.036927327179538977 0.99049231789707992 -0.1325192087745955 0 -0.96329932316107292 6.106226635438361e-16 -0.26842953264761793 0
		 -0.82905000000000073 19.120899999999992 -0.42458199999999768 1;
	setAttr ".wm[92]" -type "matrix" -0.036696171561761748 0.6396909319227414 0.76775575713147481 0
		 0.030540233855147869 0.76863223430702809 -0.63896148749377546 0 -0.998859692403684 1.3253287356462806e-15 -0.047742170993969019 0
		 -0.87711600000000045 18.645800000000001 -0.27090799999999915 1;
	setAttr ".wm[93]" -type "matrix" -0.036696171561761748 0.6396909319227414 0.76775575713147481 0
		 0.030540233855147869 0.76863223430702809 -0.63896148749377546 0 -0.998859692403684 1.3253287356462806e-15 -0.047742170993969019 0
		 -0.90228500000000045 18.238600000000002 0.078770200000001012 1;
	setAttr ".wm[94]" -type "matrix" -0.035929884258228018 0.64563704750790341 0.76279869317039828 0
		 0.030377573290521279 0.76364442176007341 -0.6449220109096151 0 -0.9988925099619923 1.3153421494355166e-13 -0.047050542418028064 0
		 -0.91741500000000031 17.917399999999997 0.402758 1;
	setAttr ".wm[95]" -type "matrix" -0.035929884258228018 0.64563704750790341 0.76279869317039828 0
		 0.030377573290521279 0.76364442176007341 -0.6449220109096151 0 -0.9988925099619923 1.3153421494355166e-13 -0.047050542418028064 0
		 -0.92533300000000007 17.582799999999999 0.75256099999999981 1;
	setAttr ".wm[96]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.92033100000000023 17.195499999999992 1.0309399999999997 1;
	setAttr ".wm[97]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.92029100000000008 16.867799999999995 1.1724399999999993 1;
	setAttr ".wm[98]" -type "matrix" -0.097065876695656 0.34562115118083336 0.93334036419611643 0
		 0.035751219841574991 0.93837413639573164 -0.34376711655334896 0 -0.99463564477709243 2.4945323584546486e-15 -0.10344048597554503 0
		 -0.91044100000000017 16.564099999999996 1.2732300000000005 1;
	setAttr ".wm[99]" -type "matrix" 0.99931697839817979 -0.03678642920521661 0.0035121662063207909 0
		 -0.03516833938310835 -0.91754632161655481 0.39607061945183958 0 -0.011347448619215661 -0.39592361171602164 -0.91821333528520233 0
		 -0.8856590000000002 16.093099999999996 1.4386899999999982 1;
	setAttr -s 100 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[3]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 11.290417510307522 -0.30575371918217331 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.13615652300521427 0 0 0.99068733778277929 1
		 1 1 yes;
	setAttr ".xm[4]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0.73294791973833107 -2.7755575615628914e-17 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.061460274103232897 0.061460274103232904 0.70443071675442681 0.70443071675442692 1
		 1 1 yes;
	setAttr ".xm[5]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6059012883365249 -3.3833774298022766e-31
		 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.11368981806260474 0 0.99351629340886594 1
		 1 1 yes;
	setAttr ".xm[6]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.6294198485169147 4.221638438096821e-31
		 -1.1102230246251565e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.013839369459957052 0 0.99990423134065731 1
		 1 1 yes;
	setAttr ".xm[7]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.2179155821930434 -2.0337820212729211e-31
		 2.7755575615628914e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.1007574452602511 0 0.9949110197523332 1
		 1 1 yes;
	setAttr ".xm[8]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.1251701128334721 -1.5264800368591707e-30
		 -8.3266726846886741e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.035296879408558003 0 0.99937687100713801 1
		 1 1 yes;
	setAttr ".xm[9]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.90920262879895186 1.5490976766435683e-30
		 -3.8857805861880479e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.065907826308504211 0 0.99782571545901144 1
		 1 1 yes;
	setAttr ".xm[10]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.0924359929576617 4.1099345013223613e-31
		 -2.2204460492503131e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.034216436942996496 0 0.99941444628488629 1
		 1 1 yes;
	setAttr ".xm[11]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.2750054547438887 2.011838456969059e-30
		 -1.5612511283791264e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[12]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.38813223676744352 -1.0148639098398196e-16
		 0.18495873319083661 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.99614952772992371 0 -0.087670510455055223 1
		 1 1 yes;
	setAttr ".xm[13]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.1036875395607693 -0.59846639999999973
		 0.32383580444340093 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20888082964928789 0.055577584331834254 -0.6499651278761428 0.7285775618764363 1
		 1 1 yes;
	setAttr ".xm[14]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.4163909364405824 4.3298697960381105e-15
		 -5.5511151231257857e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619629083776 -0.19151262312050488 -0.035651083353537324 0.98082693497125062 1
		 1 1 yes;
	setAttr ".xm[15]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[16]" -type "matrix" "xform" 1 1 1 0 0 0 3 2.763029379803347 -2.9901889802249744e-15
		 6.1977251948291957e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424696022538 6.0215466624456995e-05 0.00028513614521740702 0.99999896722879134 1
		 1 1 yes;
	setAttr ".xm[17]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.3262893058653958e-31 1.1843548872543966e-16
		 1.1748840317954808e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.70710678118654746 0 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[18]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.29999999999999988 2.7829707478258147e-15
		 -3.1086244689504375e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[19]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401444 -0.29225669056177106
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[20]" -type "matrix" "xform" 1 1 1 0 0 0 3 0.85619999999999941 -0.40510070369043732
		 0.42465902716735693 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071632605204258515 -0.070855182925839061 -0.70358843558290385 0.70342847983160206 1
		 1 1 yes;
	setAttr ".xm[21]" -type "matrix" "xform" 1 1 1 0 0 0 3 5.1039432420868449 1.1584700213007615e-16
		 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.00038254971319926455 -0.030667825540422869 5.7912800117392978e-05 0.99952955673078858 1
		 1 1 yes;
	setAttr ".xm[22]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.5943197435413126 1.3242089580900104e-17
		 -4.8572257327350599e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156972832253 -0.48052832367267562 0.0038217968106755776 0.87696843816418957 1
		 1 1 yes;
	setAttr ".xm[23]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[24]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.1282257310760708 1.0961885143939659e-15
		 -4.7610535965885447e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[25]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.2564514621521417 2.1923770287879319e-15
		 -9.5221071931770894e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[26]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.3846771932282129 3.288565543181897e-15
		 -1.4283160789765633e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.079181153912334629 0.99686024339679191 1
		 1 1 yes;
	setAttr ".xm[27]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.10915409999999959 -7.0518867354993834e-16
		 -4.5520648033906218e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349093526172 0.051920268595790221 0.075303689671793003 0.99579767338342862 1
		 1 1 yes;
	setAttr ".xm[28]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.67809966018133316 4.0050428251614534e-16
		 1.5265566588595902e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226642272568 -0.068108891780257405 -0.10891411752763996 0.99169500809891153 1
		 1 1 yes;
	setAttr ".xm[29]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.35468834509693448 -1.5543122344752148e-15
		 6.8782774695160208e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[30]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.44035893053684116 2.2204460492503151e-15
		 -4.1693089501269e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[31]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.62990893714498686 -1.3322676295501873e-15
		 -9.6748875453842723e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[32]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[33]" -type "matrix" "xform" 1 1 1 0 0 0 5 -0.076525269383702535 0.023547569757453157
		 0.19836057277298721 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886703781422 -0.079692662965438754 -0.19114093582264557 0.9230540437946958 1
		 1 1 yes;
	setAttr ".xm[34]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.78036916329648875 1.0269562977782698e-15
		 -1.3877787807814457e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348613168178 0.020782185645402684 0.043527662293890997 0.72745918696323897 1
		 1 1 yes;
	setAttr ".xm[35]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.35245262105826525 4.4408920985006153e-16
		 2.2204460492503348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[36]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.38733069761372629 -8.8817841970012326e-16
		 -3.944304526105059e-30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[37]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.9009795642339747e-16 1.6524790809532086e-18
		 1.8957551425785906e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0023408149950071714 -0.54279005697380478 0.0036618570973429849 0.83985716966525426 1
		 1 1 yes;
	setAttr ".xm[38]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.59601991577807734 1.8175355256292112e-27
		 -8.0491169285323849e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[39]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6633421254816507 5.0487097934144756e-28
		 5.5511151231257827e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491503 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[40]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.89886392169674756 1.1102230246223798e-16
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[41]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[42]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[43]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.1036875399999999 0.59846639999999995
		 0.32383580439999998 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.64996512791127337 0.72857756184195677 -0.2088808297181233 -0.055577584114279266 1
		 1 1 yes;
	setAttr ".xm[44]" -type "matrix" "xform" 1 1 1 0 0 0 3 -1.416390936 4.1969983040000001e-10
		 2.1459101160000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619623608 -0.19151262309887584 -0.035651083397193438 0.98082693497388995 1
		 1 1 yes;
	setAttr ".xm[45]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.3256375430000002e-10 -2.593480986e-11
		 1.3505818690000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[46]" -type "matrix" "xform" 1 1 1 0 0 0 3 -2.7630293799999999 -6.8785510619999996e-10
		 5.9058447019999997e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424698124646 6.0215462682850012e-05 0.00028513614109331641 0.99999896722879245 1
		 1 1 yes;
	setAttr ".xm[47]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.359117263e-10 8.1712414610000005e-14
		 -1.6875389970000001e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.70710678118654746 0 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[48]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.29999999999999999 1.111288839e-10
		 5.1685766779999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[49]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401433 0.29144088923931144
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[50]" -type "matrix" "xform" 1 1 1 0 0 0 3 -0.85619999999999996 -0.40510070370000001
		 0.42465902719999998 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.7034284798323589 0.70358843558220097 -0.070855182932823474 0.071632605196822852 1
		 1 1 yes;
	setAttr ".xm[51]" -type "matrix" "xform" 1 1 1 0 0 0 3 -5.1039432419999997 -2.9864999360000001e-14
		 2.6777802200000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.00038254971320976207 -0.030667825540029232 5.7912799514840228e-05 0.99952955673080068 1
		 1 1 yes;
	setAttr ".xm[52]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.5943197439999999 -1.129296656e-11
		 -2.2188917369999999e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156974160557 -0.48052832367275899 0.0038217968109156681 0.87696843816414249 1
		 1 1 yes;
	setAttr ".xm[53]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.0874435509999999e-10 -3.3715252810000002e-12
		 -3.2691249709999998e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[54]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.1282257309999999 -2.7998581230000002e-10
		 1.9434587269999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[55]" -type "matrix" "xform" 1 1 1 0 0 0 0 -2.2564514619999998 -5.6006399520000001e-10
		 3.8870950899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[56]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.3846771929999999 -8.4013862530000004e-10
		 5.8307136899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.079181153912334629 0.99686024339679191 1
		 1 1 yes;
	setAttr ".xm[57]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.1091541004 -8.4579454550000004e-11
		 1.21866961e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349092261559 0.051920268596349434 0.075303689673768381 0.99579767338325065 1
		 1 1 yes;
	setAttr ".xm[58]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.6780996601 -1.4295409300000001e-10
		 1.2093082090000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226671807475 -0.068108891780949685 -0.10891411756533778 0.9916950080947049 1
		 1 1 yes;
	setAttr ".xm[59]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.35468834510000002 -1.2705569930000001e-10
		 3.5710101540000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[60]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.44035893059999998 -1.4656365009999999e-10
		 3.7431391319999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[61]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.62990893709999995 -2.0963852879999999e-10
		 5.3545612389999999e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[62]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.5955682879999998e-10 -5.7475801900000001e-11
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[63]" -type "matrix" "xform" 1 1 1 0 0 0 5 0.076525269009999994 -0.02354756987
		 -0.1983605728 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886706096509 -0.07969266291038643 -0.19114093584315128 0.92305404378707212 1
		 1 1 yes;
	setAttr ".xm[64]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.78036916329999995 -2.329372251e-10
		 -2.343245598e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348614366042 0.020782185649366937 0.043527662292334027 0.72745918695194833 1
		 1 1 yes;
	setAttr ".xm[65]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.35245262100000002 -1.1430856259999999e-10
		 9.2377661080000006e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[66]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.3873306977 -1.2523138080000001e-10
		 1.005204808e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[67]" -type "matrix" "xform" 1 1 1 0 0 0 0 -7.0798478190000004e-11 6.5503158450000003e-15
		 4.3484105210000001e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.002340814995055578 -0.5427900569738866 0.0036618570974149794 0.83985716966520096 1
		 1 1 yes;
	setAttr ".xm[68]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.59601991580000002 -1.1653567000000001e-11
		 -6.323830348e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[69]" -type "matrix" "xform" 1 1 1 0 0 0 3 -1.663342125 -3.3700819910000002e-11
		 -3.2867686350000002e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491506 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[70]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.89886392189999997 -1.8376633549999999e-11
		 1.0505785129999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[71]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.5912604569999999e-11 -3.1197266989999997e-14
		 3.0063063150000003e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[72]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.47564845123849153 1.0631297916735791e-16
		 -0.027659795107475748 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.96547823737110805 0 0.26048372917089935 1
		 1 1 yes;
	setAttr ".xm[73]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.18370230684547595 9.8607613152626476e-31
		 6.6613381477509392e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.41828403814789133 0 0.90831627940420256 1
		 1 1 yes;
	setAttr ".xm[74]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.20377879650171854 5.8355677314933246e-31
		 -6.9388939039072284e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19820660803431642 0 0.98016026267724754 1
		 1 1 yes;
	setAttr ".xm[75]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.23857368387367603 -3.9313044989804452e-31
		 3.5492442318485473e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[76]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21644808540609339 -0.62273925060932223
		 -0.20008910385773135 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.08571835649344578 -0.55642581752290021 -0.82178796751819183 0.087790713611145488 1
		 1 1 yes;
	setAttr ".xm[77]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.46604061213981773 -0.043102149571323196
		 -0.0024236635249148164 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[78]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.51599341270102894 0.019575876830657486
		 0.063902156957241218 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122638 -0.064517222783691514 -0.64525574015412179 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[79]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.041146744595169038 0.51379606264634836
		 -0.027816466552018193 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[80]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.094056821136732097 0.49265693025971274
		 -0.0050510980859091257 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912757 0.10223239472282354 0.27275670110683287 0.95556889816367396 1
		 1 1 yes;
	setAttr ".xm[81]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.0088985359227593489 0.53719893109528427
		 -0.0084463564032919228 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[82]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.043815384167760076 0.45437941922514219
		 0.00035575206024950762 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411100415487 0.00026524166420574817 0.0038805462674768852 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[83]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.051103465102685583 0.48132864421422783
		 0.0085485235017488601 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[84]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.037875747802228063 0.47511833912037177
		 0.018094152051907897 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084785637 -0.024433420154250138 -0.17352495576627536 0.98442348766544641 1
		 1 1 yes;
	setAttr ".xm[85]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.018793975249772624 0.35619597747174936
		 0.01467763363979435 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[86]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.011852099687511403 0.31926408905670134
		 0.020222390563214634 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[87]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.010747678320721432 0.49793861709289661
		 0.04176416876903332 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.66815275056484158 0.020937923968194282 -0.74349139430409505 0.018816265524581065 1
		 1 1 yes;
	setAttr ".xm[88]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21643563291215034 0.62273900000000193
		 -0.20008927233585919 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.82178796751819183 0.087790713611145405 -0.08571835649344553 0.55642581752290021 1
		 1 1 yes;
	setAttr ".xm[89]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.46603798592048273 0.043102888250008409
		 0.0024249419964386121 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[90]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.51604232130763428 -0.019576307319524755
		 -0.063915819607909596 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122641 -0.064517222783691486 -0.6452557401541219 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[91]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.04113712082946322 -0.51372518225503505
		 0.027816828879492217 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[92]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.094047681809646982 -0.49272260603033041
		 0.0050513052669699521 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912292 0.10223239472282343 0.2727567011068327 0.95556889816367407 1
		 1 1 yes;
	setAttr ".xm[93]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.0089089096564693923 -0.53718661577186799
		 0.0084459031808444829 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[94]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.043829984432502161 -0.45436247401548463
		 -0.00035513380149254647 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411086023657 0.0002652416642052489 0.0038805462674778783 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[95]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.051083607994496634 -0.48135160732845123
		 -0.0085491899956186002 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[96]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.037887812374790837 -0.47514028040108791
		 -0.018094343282668901 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084644157 -0.02443342015422496 -0.17352495576627963 0.98442348766544829 1
		 1 1 yes;
	setAttr ".xm[97]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.018803727656725167 -0.35614682144038068
		 -0.014676614191331594 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[98]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.011849867191743121 -0.31928036338535581
		 -0.020222927682530312 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[99]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.010762552102557693 -0.49796793861719396
		 -0.04176432335838054 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.66815275056484258 -0.020937923968192444 0.74349139430409417 -0.01881626552457839 1
		 1 1 yes;
	setAttr -s 97 ".m";
	setAttr -s 100 ".p";
	setAttr -s 100 ".g[0:99]" yes yes yes no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no no no no no no no no no no no no no no no no no no no no no no no no no no 
		no no;
	setAttr -l on ".amt" 100663296;
createNode expression -n "ROOL_expr";
	setAttr -k on ".nds";
	setAttr -s 34 ".in[0:33]"  -1 0 -1 0 -0.5 0 0 -0.5 0 0 -1 0 0 0 0 0 0.33 0 0.66 
		0.33 0 0.66 -0.5 0 -0.5 0 -0.5 0 -0.5 0 -0.5 0 -0.5 0;
	setAttr -s 17 ".in";
	setAttr -s 19 ".out";
	setAttr ".ixp" -type "string" "//ROLL_expr//\r\n\r\n\r\n///  Torsions\r\n\r\n.O[0] =  .I[0] * .I[1];\r\n.O[1] =   .I[2] * .I[3];\r\n\r\n.O[2] =  .I[4] * .I[5];\r\n.O[3] =   .I[4] * .I[6];\r\n.O[4] =  .I[7] * .I[8];\r\n.O[5] =  .I[7] * .I[9];\r\n\r\n\r\n.O[6] =        .I[10] * .I[11];\r\n\r\n\r\n.O[7] =      .I[12] * .I[13];\r\n.O[8] =     .I[14] * .I[15];\r\n\r\n\r\n.O[9]  =   .I[16] * .I[17];\r\n.O[10]  =   .I[18] * .I[17];\r\n\r\n.O[11]  =  .I[19] * .I[20];\r\n.O[12]  =  .I[21] * .I[20];\r\n\r\n\r\n//  Interpolation Spherique\r\n\r\n.O[13] =     .I[22] * .I[23];\r\n.O[14] =      .I[24] * .I[25];\r\n\r\n.O[15]     = .I[26] * .I[27];\r\n.O[16]     = .I[28] * .I[29];\r\n\r\n.O[17]     = .I[30] * .I[31];\r\n.O[18]     = .I[32] * .I[33];";
createNode unitConversion -n "unitConversion1";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion2";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion3";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion4";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion5";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion6";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion7";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion8";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion9";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion10";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion11";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion12";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion13";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion14";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion15";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion16";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion17";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion18";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion19";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion20";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion21";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion22";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion23";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion24";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion25";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion26";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion27";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion28";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion29";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion30";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion31";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion32";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion33";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion34";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion35";
	setAttr ".cf" 57.295779513082323;
createNode unitConversion -n "unitConversion36";
	setAttr ".cf" 0.017453292519943295;
createNode dagPose -n "bindPose1";
	setAttr -s 102 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[2]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[3]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[4]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[5]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[6]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[7]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[8]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[9]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[10]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[11]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[12]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[13]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[14]" -type "matrix" -2.2204460492503131e-16 -0.99244361258999358 0.12270157223655645 0
		 -1 1.1102230246251565e-16 0 0 -2.0816681711721685e-17 -0.12270157223655645 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[15]" -type "matrix" -2.2204460492503131e-16 -0.99244361258999358 0.12270157223655645 0
		 -1 1.1102230246251565e-16 0 0 -2.0816681711721685e-17 -0.12270157223655645 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[16]" -type "matrix" 1 1.093444474054003e-16 -2.7245222130946367e-17 0
		 1.118986869801765e-16 0.99999999999999989 -4.163336342344337e-16 0 1.4230842380892528e-17 4.3021142204224816e-16 0.99999999999999989 0
		 3.944304526105059e-31 0 1.6653345369377348e-16 1;
	setAttr ".wm[17]" -type "matrix" 1 1.093444474054003e-16 -2.7245222130946367e-17 0
		 1.118986869801765e-16 0.99999999999999989 -4.163336342344337e-16 0 1.4230842380892528e-17 4.3021142204224816e-16 0.99999999999999989 0
		 3.944304526105059e-31 0 1.6653345369377348e-16 1;
	setAttr ".wm[18]" -type "matrix" -2.2204460492503131e-16 -0.99244361258999358 0.12270157223655645 0
		 -1 1.1102230246251565e-16 0 0 -2.0816681711721685e-17 -0.12270157223655645 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[19]" -type "matrix" -2.2204460492503131e-16 -0.99244361258999358 0.12270157223655645 0
		 -1 1.1102230246251565e-16 0 0 -2.0816681711721685e-17 -0.12270157223655645 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260767 1;
	setAttr ".wm[20]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[21]" -type "matrix" 2.2204460492503131e-16 0.99861931185935626 0.052530657539630266 0
		 -1 2.2204460492503131e-16 3.4694469519536142e-18 0 -3.4694469519536142e-18 -0.052530657539630266 0.99861931185935615 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr ".wm[22]" -type "matrix" -2.1923727666465254e-16 -0.9924436125899937 0.12270157223655612 0
		 -1 2.2204460492503131e-16 3.4694469519536142e-18 0 -3.5367501454474542e-17 -0.12270157223655612 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260656 1;
	setAttr ".wm[23]" -type "matrix" -2.1923727666465254e-16 -0.9924436125899937 0.12270157223655612 0
		 -1 2.2204460492503131e-16 3.4694469519536142e-18 0 -3.5367501454474542e-17 -0.12270157223655612 -0.99244361258999358 0
		 1.6713595139357471e-15 19.13526856086153 -0.044841836090260656 1;
	setAttr ".wm[24]" -type "matrix" 1 -1.6778550571153304e-18 -3.0714669082899907e-17 0
		 1.1089798043948669e-16 0.99999999999999989 -8.3266726846886741e-17 0 2.9016174083868565e-17 8.3266726846886741e-17 0.99999999999999978 0
		 1.9811789827474832e-17 0 -5.9396931817445875e-15 1;
	setAttr ".wm[25]" -type "matrix" 1 -1.6778550571153304e-18 -3.0714669082899907e-17 0
		 1.1089798043948669e-16 0.99999999999999989 -8.3266726846886741e-17 0 2.9016174083868565e-17 8.3266726846886741e-17 0.99999999999999978 0
		 1.9811789827474832e-17 0 -5.9396931817445875e-15 1;
	setAttr ".wm[26]" -type "matrix" 2.2204460492503131e-16 0.99861931185935626 0.052530657539630266 0
		 -1 2.2204460492503131e-16 3.4694469519536142e-18 0 -3.4694469519536142e-18 -0.052530657539630266 0.99861931185935615 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr ".wm[27]" -type "matrix" 2.2204460492503131e-16 0.99861931185935626 0.052530657539630266 0
		 -1 2.2204460492503131e-16 3.4694469519536142e-18 0 -3.4694469519536142e-18 -0.052530657539630266 0.99861931185935615 0
		 1.6512366162151641e-15 19.532580911924878 -0.20915635734195098 1;
	setAttr ".wm[28]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[29]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[30]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[31]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[32]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[33]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[131]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 132 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[3]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[4]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 -2.7755575615628914e-17 0
		 0 0 0 0 -2.7755575615628914e-17 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[5]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[6]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[7]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[8]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[9]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[10]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 8.8817841970012523e-16
		 -2.7755575615628914e-17 0 0 0 0 8.8817841970012523e-16 -2.7755575615628914e-17 0
		 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[11]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[12]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[13]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[14]" -type "matrix" "xform" 1 1 1 0 -3.018581083961168 1.5707963267948966 0 1.6713595139357471e-15
		 19.13526856086153 -0.044841836090260767 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[15]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[16]" -type "matrix" "xform" 1 0.99999999999999978 0.99999999999999978 -3.0185810839611684
		 1.362261106547318e-17 -1.5707963267948968 0 18.99617722221139 -2.594588808030935e-15
		 2.3034245437818712 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[17]" -type "matrix" "xform" 1 0.99999999999999978 0.99999999999999978 -3.0185810839611684
		 1.362261106547318e-17 -1.5707963267948968 0 18.99617722221139 -2.594588808030935e-15
		 2.3034245437818712 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[18]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[19]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[20]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[21]" -type "matrix" "xform" 1 1 1 0 -0.052554847051387993 1.5707963267948966 0 1.6512366162151641e-15
		 19.532580911924878 -0.20915635734195098 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[22]" -type "matrix" "xform" 1 1 1 1.2012960071139389e-16 3.3171590702698062
		 0 0 -0.38813223676744418 -1.0694727140538488e-16 0.18495873319083672 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[23]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[24]" -type "matrix" "xform" 1 0.99999999999999978 0.99999999999999978 -3.0185810839611684
		 1.362261106547318e-17 -1.5707963267948968 0 18.99617722221139 -2.594588808030935e-15
		 2.3034245437818712 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[25]" -type "matrix" "xform" 1 0.99999999999999978 0.99999999999999978 -3.0185810839611684
		 1.362261106547318e-17 -1.5707963267948968 0 18.99617722221139 -2.594588808030935e-15
		 2.3034245437818712 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[26]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[27]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[28]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[29]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[30]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 -0.29144088923931122
		 19.851563453674316 0.41745445877313614 0 0 0 -0.29144088923931122 19.851563453674316
		 0.41745445877313614 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[31]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0.29225669056177139
		 19.851563453674316 0.41745445877313614 0 0 0 0.29225669056177139 19.851563453674316
		 0.41745445877313614 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[32]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[33]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[34]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 11.290417510307522 -0.30575371918217331 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.13615652300521427 0 0 0.99068733778277929 1
		 1 1 yes;
	setAttr ".xm[35]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0.73294791973833107 -2.7755575615628914e-17 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.061460274103232897 0.061460274103232904 0.70443071675442681 0.70443071675442692 1
		 1 1 yes;
	setAttr ".xm[36]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6059012883365249 -3.3833774298022766e-31
		 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.11368981806260474 0 0.99351629340886594 1
		 1 1 yes;
	setAttr ".xm[37]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.6294198485169147 4.221638438096821e-31
		 -1.1102230246251565e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.013839369459957052 0 0.99990423134065731 1
		 1 1 yes;
	setAttr ".xm[38]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.2179155821930434 -2.0337820212729211e-31
		 2.7755575615628914e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.1007574452602511 0 0.9949110197523332 1
		 1 1 yes;
	setAttr ".xm[39]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.1251701128334721 -1.5264800368591707e-30
		 -8.3266726846886741e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.035296879408558003 0 0.99937687100713801 1
		 1 1 yes;
	setAttr ".xm[40]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.90920262879895186 1.5490976766435683e-30
		 -3.8857805861880479e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.065907826308504211 0 0.99782571545901144 1
		 1 1 yes;
	setAttr ".xm[41]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.0924359929576617 4.1099345013223613e-31
		 -2.2204460492503131e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.034216436942996496 0 0.99941444628488629 1
		 1 1 yes;
	setAttr ".xm[42]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.2750054547438887 2.011838456969059e-30
		 -1.5612511283791264e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[43]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21643563291215034 0.62273900000000193
		 -0.20008927233585919 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.82178796751819183 0.087790713611145405 -0.08571835649344553 0.55642581752290021 1
		 1 1 yes;
	setAttr ".xm[44]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.46603798592048273 0.043102888250008409
		 0.0024249419964386121 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[45]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.51604232130763428 -0.019576307319524755
		 -0.063915819607909596 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122641 -0.064517222783691486 -0.6452557401541219 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[46]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.04113712082946322 -0.51372518225503505
		 0.027816828879492217 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[47]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.094047681809646982 -0.49272260603033041
		 0.0050513052669699521 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912292 0.10223239472282343 0.2727567011068327 0.95556889816367407 1
		 1 1 yes;
	setAttr ".xm[48]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.0089089096564693923 -0.53718661577186799
		 0.0084459031808444829 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[49]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.043829984432502161 -0.45436247401548463
		 -0.00035513380149254647 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411086023657 0.0002652416642052489 0.0038805462674778783 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[50]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.051083607994496634 -0.48135160732845123
		 -0.0085491899956186002 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[51]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.037887812374790837 -0.47514028040108791
		 -0.018094343282668901 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084644157 -0.02443342015422496 -0.17352495576627963 0.98442348766544829 1
		 1 1 yes;
	setAttr ".xm[52]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.018803727656725167 -0.35614682144038068
		 -0.014676614191331594 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[53]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.011849867191743121 -0.31928036338535581
		 -0.020222927682530312 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[54]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.010762552102557693 -0.49796793861719396
		 -0.04176432335838054 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.66815275056484258 -0.020937923968192444 0.74349139430409417 -0.01881626552457839 1
		 1 1 yes;
	setAttr ".xm[55]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.21644808540609339 -0.62273925060932223
		 -0.20008910385773135 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.08571835649344578 -0.55642581752290021 -0.82178796751819183 0.087790713611145488 1
		 1 1 yes;
	setAttr ".xm[56]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.46604061213981773 -0.043102149571323196
		 -0.0024236635249148164 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[57]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.51599341270102894 0.019575876830657486
		 0.063902156957241218 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.12337082149122638 -0.064517222783691514 -0.64525574015412179 0.75117388011499431 1
		 1 1 yes;
	setAttr ".xm[58]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.041146744595169038 0.51379606264634836
		 -0.027816466552018193 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[59]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.094056821136732097 0.49265693025971274
		 -0.0050510980859091257 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.045170790703912757 0.10223239472282354 0.27275670110683287 0.95556889816367396 1
		 1 1 yes;
	setAttr ".xm[60]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.0088985359227593489 0.53719893109528427
		 -0.0084463564032919228 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[61]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.043815384167760076 0.45437941922514219
		 0.00035575206024950762 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.00022249411100415487 0.00026524166420574817 0.0038805462674768852 0.99999241072314948 1
		 1 1 yes;
	setAttr ".xm[62]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.051103465102685583 0.48132864421422783
		 0.0085485235017488601 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[63]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.037875747802228063 0.47511833912037177
		 0.018094152051907897 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.014230061084785637 -0.024433420154250138 -0.17352495576627536 0.98442348766544641 1
		 1 1 yes;
	setAttr ".xm[64]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.018793975249772624 0.35619597747174936
		 0.01467763363979435 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[65]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.011852099687511403 0.31926408905670134
		 0.020222390563214634 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[66]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.010747678320721432 0.49793861709289661
		 0.04176416876903332 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.66815275056484158 0.020937923968194282 -0.74349139430409505 0.018816265524581065 1
		 1 1 yes;
	setAttr ".xm[67]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401444 -0.29225669056177106
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[68]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.35145840449401433 0.29144088923931144
		 0.60898929957919268 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.70710678118654746 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[69]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.38813223676744352 -1.0148639098398196e-16
		 0.18495873319083661 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.99614952772992371 0 -0.087670510455055223 1
		 1 1 yes;
	setAttr ".xm[70]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.47564845123849153 1.0631297916735791e-16
		 -0.027659795107475748 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.96547823737110805 0 0.26048372917089935 1
		 1 1 yes;
	setAttr ".xm[71]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.18370230684547595 9.8607613152626476e-31
		 6.6613381477509392e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.41828403814789133 0 0.90831627940420256 1
		 1 1 yes;
	setAttr ".xm[72]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.20377879650171854 5.8355677314933246e-31
		 -6.9388939039072284e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19820660803431642 0 0.98016026267724754 1
		 1 1 yes;
	setAttr ".xm[73]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.23857368387367603 -3.9313044989804452e-31
		 3.5492442318485473e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[74]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[75]" -type "matrix" "xform" 1 1 1 1.4274156856758724e-10 -1.0741296741751788e-11
		 -0.52951544211162549 0 1.1036875395607693 -0.59846639999999973 0.32383580444340093 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20888082964928789 0.055577584331834254 -0.6499651278761428 0.7285775618764363 1
		 1 1 yes;
	setAttr ".xm[76]" -type "matrix" "xform" 1 1 1 -0.057417913726941099 -0.15413224005414905
		 -0.3789828778757085 3 1.4163909364405824 4.3298697960381105e-15 -5.5511151231257857e-16 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619629083776 -0.19151262312050488 -0.035651083353537324 0.98082693497125062 1
		 1 1 yes;
	setAttr ".xm[77]" -type "matrix" "xform" 1 1 1 0.0028423938112721705 0.033282805334109884
		 -0.085474000382206192 3 2.763029379803347 -2.9901889802249744e-15 6.1977251948291957e-17 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424696022538 6.0215466624456995e-05 0.00028513614521740702 0.99999896722879134 1
		 1 1 yes;
	setAttr ".xm[78]" -type "matrix" "xform" 1 1 1 0 0 0.15852825595864495 0 3.3846771932282129
		 3.288565543181897e-15 -1.4283160789765633e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0 -0.079181153912334629 0.99686024339679191 1 1 1 yes;
	setAttr ".xm[79]" -type "matrix" "xform" 1 1 1 0 0 0 5 -0.076525269383702535 0.023547569757453157
		 0.19836057277298721 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886703781422 -0.079692662965438754 -0.19114093582264557 0.9230540437946958 1
		 1 1 yes;
	setAttr ".xm[80]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.78036916329648875 1.0269562977782698e-15
		 -1.3877787807814457e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348613168178 0.020782185645402684 0.043527662293890997 0.72745918696323897 1
		 1 1 yes;
	setAttr ".xm[81]" -type "matrix" "xform" 1 1 1 0 0 0 1 0.35245262105826525 4.4408920985006153e-16
		 2.2204460492503348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[82]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.38733069761372629 -8.8817841970012326e-16
		 -3.944304526105059e-30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[83]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.10915409999999959 -7.0518867354993834e-16
		 -4.5520648033906218e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349093526172 0.051920268595790221 0.075303689671793003 0.99579767338342862 1
		 1 1 yes;
	setAttr ".xm[84]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.67809966018133316 4.0050428251614534e-16
		 1.5265566588595902e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226642272568 -0.068108891780257405 -0.10891411752763996 0.99169500809891153 1
		 1 1 yes;
	setAttr ".xm[85]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.35468834509693448 -1.5543122344752148e-15
		 6.8782774695160208e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[86]" -type "matrix" "xform" 1 1 1 0 0 0 2 0.44035893053684116 2.2204460492503151e-15
		 -4.1693089501269e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[87]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.62990893714498686 -1.3322676295501873e-15
		 -9.6748875453842723e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[88]" -type "matrix" "xform" 1 1 1 0 0 -0.079264127979322474 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[89]" -type "matrix" "xform" 1 1 1 0 -0.016641402667054942 0 0 1.3262893058653958e-31
		 1.1843548872543966e-16 1.1748840317954808e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0.70710678118654746 0 0.70710678118654757 1 1 1 yes;
	setAttr ".xm[90]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.29999999999999988 2.7829707478258147e-15
		 -3.1086244689504375e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[91]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.1282257310760708 1.0961885143939659e-15
		 -4.7610535965885447e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[92]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.2564514621521417 2.1923770287879319e-15
		 -9.5221071931770894e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[93]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[94]" -type "matrix" "xform" 1 1 1 4.7184478542310744e-16 2.7755575620310616e-16
		 -0.5295154417625596 0 1.1036875399999999 0.59846639999999995 0.32383580439999998 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.64996512791127337 0.72857756184195677 -0.2088808297181233 -0.055577584114279266 1
		 1 1 yes;
	setAttr ".xm[95]" -type "matrix" "xform" 1 1 1 -0.057417913761847683 -0.15413224001924247
		 -0.37898287822477439 3 -1.416390936 4.1969983040000001e-10 2.1459101160000001e-10 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0055171619623608 -0.19151262309887584 -0.035651083397193438 0.98082693497388995 1
		 1 1 yes;
	setAttr ".xm[96]" -type "matrix" "xform" 1 1 1 0.0028423938042908535 0.033282805264296708
		 -0.085474000329846311 3 -2.7630293799999999 -6.8785510619999996e-10 5.9058447019999997e-10 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0014073424698124646 6.0215462682850012e-05 0.00028513614109331641 0.99999896722879245 1
		 1 1 yes;
	setAttr ".xm[97]" -type "matrix" "xform" 1 1 1 0 0 0.15852825595864495 0 -3.3846771929999999
		 -8.4013862530000004e-10 5.8307136899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0 -0.079181153912334629 0.99686024339679191 1 1 1 yes;
	setAttr ".xm[98]" -type "matrix" "xform" 1 1 1 0 0 0 5 0.076525269009999994 -0.02354756987
		 -0.1983605728 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.32416886706096509 -0.07969266291038643 -0.19114093584315128 0.92305404378707212 1
		 1 1 yes;
	setAttr ".xm[99]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.78036916329999995 -2.329372251e-10
		 -2.343245598e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.68445348614366042 0.020782185649366937 0.043527662292334027 0.72745918695194833 1
		 1 1 yes;
	setAttr ".xm[100]" -type "matrix" "xform" 1 1 1 0 0 0 1 -0.35245262100000002 -1.1430856259999999e-10
		 9.2377661080000006e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[101]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.3873306977 -1.2523138080000001e-10
		 1.005204808e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[102]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.1091541004 -8.4579454550000004e-11
		 1.21866961e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0045424349092261559 0.051920268596349434 0.075303689673768381 0.99579767338325065 1
		 1 1 yes;
	setAttr ".xm[103]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.6780996601 -1.4295409300000001e-10
		 1.2093082090000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.0063170226671807475 -0.068108891780949685 -0.10891411756533778 0.9916950080947049 1
		 1 1 yes;
	setAttr ".xm[104]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.35468834510000002 -1.2705569930000001e-10
		 3.5710101540000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[105]" -type "matrix" "xform" 1 1 1 0 0 0 2 -0.44035893059999998 -1.4656365009999999e-10
		 3.7431391319999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[106]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.62990893709999995 -2.0963852879999999e-10
		 5.3545612389999999e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[107]" -type "matrix" "xform" 1 1 1 0 0 -0.079264127979322474 0 -3.5955682879999998e-10
		 -5.7475801900000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[108]" -type "matrix" "xform" 1 1 1 0 -0.016641402632148354 0 0 -1.359117263e-10
		 8.1712414610000005e-14 -1.6875389970000001e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		0 0.70710678118654746 0 0.70710678118654757 1 1 1 yes;
	setAttr ".xm[109]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.29999999999999999 1.111288839e-10
		 5.1685766779999998e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[110]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.1282257309999999 -2.7998581230000002e-10
		 1.9434587269999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[111]" -type "matrix" "xform" 1 1 1 0 0 0 0 -2.2564514619999998 -5.6006399520000001e-10
		 3.8870950899999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[112]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.3256375430000002e-10 -2.593480986e-11
		 1.3505818690000001e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[113]" -type "matrix" "xform" 1 1 1 0 0 0.031415926535897934 3 0.85619999999999941
		 -0.40510070369043732 0.42465902716735693 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071632605204258515 -0.070855182925839061 -0.70358843558290385 0.70342847983160206 1
		 1 1 yes;
	setAttr ".xm[114]" -type "matrix" "xform" 1 1 1 0 0 -0.040142572795869587 3 5.1039432420868449
		 1.1584700213007615e-16 1.6653345369377348e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		-0.00038254971319926455 -0.030667825540422869 5.7912800117392978e-05 0.99952955673078858 1
		 1 1 yes;
	setAttr ".xm[115]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.5943197435413126 1.3242089580900104e-17
		 -4.8572257327350599e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156972832253 -0.48052832367267562 0.0038217968106755776 0.87696843816418957 1
		 1 1 yes;
	setAttr ".xm[116]" -type "matrix" "xform" 1 1 1 0 0 0 3 1.6633421254816507 5.0487097934144756e-28
		 5.5511151231257827e-17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491503 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[117]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.89886392169674756 1.1102230246223798e-16
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[118]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[119]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.9009795642339747e-16 1.6524790809532086e-18
		 1.8957551425785906e-18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0023408149950071714 -0.54279005697380478 0.0036618570973429849 0.83985716966525426 1
		 1 1 yes;
	setAttr ".xm[120]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.59601991577807734 1.8175355256292112e-27
		 -8.0491169285323849e-16 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[121]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[122]" -type "matrix" "xform" 1 1 1 0 0 0.031415926535897934 3 -0.85619999999999996
		 -0.40510070370000001 0.42465902719999998 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.7034284798323589 0.70358843558220097 -0.070855182932823474 0.071632605196822852 1
		 1 1 yes;
	setAttr ".xm[123]" -type "matrix" "xform" 1 1 1 0 0 -0.040142572795869587 3 -5.1039432419999997
		 -2.9864999360000001e-14 2.6777802200000001e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		-0.00038254971320976207 -0.030667825540029232 5.7912799514840228e-05 0.99952955673080068 1
		 1 1 yes;
	setAttr ".xm[124]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.5943197439999999 -1.129296656e-11
		 -2.2188917369999999e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0020694156974160557 -0.48052832367275899 0.0038217968109156681 0.87696843816414249 1
		 1 1 yes;
	setAttr ".xm[125]" -type "matrix" "xform" 1 1 1 0 0 0 3 -1.663342125 -3.3700819910000002e-11
		 -3.2867686350000002e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.19815625350491506 0 0.98017044395191588 1
		 1 1 yes;
	setAttr ".xm[126]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.89886392189999997 -1.8376633549999999e-11
		 1.0505785129999999e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[127]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.0874435509999999e-10 -3.3715252810000002e-12
		 -3.2691249709999998e-10 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[128]" -type "matrix" "xform" 1 1 1 0 0 0 0 -7.0798478190000004e-11 6.5503158450000003e-15
		 4.3484105210000001e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.002340814995055578 -0.5427900569738866 0.0036618570974149794 0.83985716966520096 1
		 1 1 yes;
	setAttr ".xm[129]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.59601991580000002 -1.1653567000000001e-11
		 -6.323830348e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[130]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.5912604569999999e-11 -3.1197266989999997e-14
		 3.0063063150000003e-11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[131]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr -s 112 ".m";
	setAttr -s 132 ".p";
	setAttr ".bp" yes;
createNode polyCube -n "polyCube1";
	setAttr ".cuv" 4;
select -ne :time1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -l on -k on ".o" 0;
select -ne :renderPartition;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".st";
	setAttr -cb on ".an";
	setAttr -cb on ".pt";
select -ne :renderGlobalsList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :defaultShaderList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".s";
select -ne :postProcessList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".p";
select -ne :lightList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :initialShadingGroup;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 16 ".dsm";
	setAttr -k on ".mwc";
	setAttr -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr ".ro" yes;
	setAttr -cb on ".mimt";
	setAttr -cb on ".miop";
	setAttr -cb on ".mise";
	setAttr -cb on ".mism";
	setAttr -cb on ".mice";
	setAttr -av -cb on ".micc";
	setAttr -cb on ".mica";
	setAttr -cb on ".micw";
	setAttr -cb on ".mirw";
select -ne :initialParticleSE;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".mwc";
	setAttr -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr ".ro" yes;
	setAttr -cb on ".mimt";
	setAttr -cb on ".miop";
	setAttr -cb on ".mise";
	setAttr -cb on ".mism";
	setAttr -cb on ".mice";
	setAttr -cb on ".micc";
	setAttr -cb on ".mica";
	setAttr -cb on ".micw";
	setAttr -cb on ".mirw";
select -ne :defaultRenderGlobals;
	setAttr -l on ".fs";
	setAttr ".ef" 10;
	setAttr -l on ".bfs";
	setAttr -k on ".mbf";
select -ne :defaultRenderQuality;
	setAttr -k on ".cch";
	setAttr -k on ".nds";
	setAttr -k on ".mvs";
	setAttr -k on ".mvm";
	setAttr -k on ".vs";
	setAttr -k on ".pss";
	setAttr ".ert" yes;
	setAttr -k on ".rct";
	setAttr -k on ".gct";
	setAttr -k on ".bct";
	setAttr -k on ".cct";
select -ne :defaultLightSet;
	setAttr -k on ".cch";
	setAttr -k on ".nds";
	setAttr -k on ".mwc";
	setAttr ".ro" yes;
select -ne :hardwareRenderGlobals;
	addAttr -ci true -sn "ani" -ln "animation" -bt "ANIM" -min 0 -max 1 -at "bool";
	setAttr -k on ".cch";
	setAttr -k on ".nds";
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
	setAttr -k off ".eeaa";
	setAttr -k off ".engm";
	setAttr -k off ".mes";
	setAttr -k off ".emb";
	setAttr -k off ".mbbf";
	setAttr -k off ".mbs";
	setAttr -k off ".trm";
	setAttr ".enpt" no;
	setAttr -k off ".clmt";
	setAttr ".hgcd" no;
	setAttr ".hgci" no;
	setAttr -k off ".twa";
	setAttr -k off ".twz";
	setAttr -k on ".hwcc";
	setAttr -k on ".hwdp";
	setAttr -k on ".hwql";
	setAttr -k on ".ani";
select -ne :defaultHardwareRenderGlobals;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".rp";
	setAttr -k on ".cai";
	setAttr -k on ".coi";
	setAttr -cb on ".bc";
	setAttr -av -k on ".bcb";
	setAttr -av -k on ".bcg";
	setAttr -av -k on ".bcr";
	setAttr -k on ".ei";
	setAttr -k on ".ex";
	setAttr -k on ".es";
	setAttr -l on -av -k on ".ef";
	setAttr -l on -k on ".bf";
	setAttr -k on ".fii";
	setAttr -l on -k on ".sf";
	setAttr -k on ".gr";
	setAttr -k on ".li";
	setAttr -k on ".ls";
	setAttr -k on ".mb";
	setAttr -k on ".ti";
	setAttr -k on ".txt";
	setAttr -k on ".mpr";
	setAttr -k on ".wzd";
	setAttr ".fn" -type "string" "im";
	setAttr -k on ".if";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
	setAttr -k on ".as";
	setAttr -k on ".ds";
	setAttr -k on ".lm";
	setAttr -k on ".fir";
	setAttr -k on ".aap";
	setAttr -k on ".gh";
	setAttr -cb on ".sd";
connectAttr "SKELETON.di" "FBX_Hips.do";
connectAttr "FBX_Hips.s" "FBX_Spine.is";
connectAttr "SKELETON.di" "FBX_Spine.do";
connectAttr "FBX_Spine.s" "FBX_Spine1.is";
connectAttr "SKELETON.di" "FBX_Spine1.do";
connectAttr "FBX_Spine1.s" "FBX_Spine2.is";
connectAttr "SKELETON.di" "FBX_Spine2.do";
connectAttr "FBX_Spine2.s" "FBX_Spine3.is";
connectAttr "SKELETON.di" "FBX_Spine3.do";
connectAttr "FBX_Spine3.s" "FBX_Neck.is";
connectAttr "SKELETON.di" "FBX_Neck.do";
connectAttr "FBX_Neck.s" "FBX_Neck1.is";
connectAttr "SKELETON.di" "FBX_Neck1.do";
connectAttr "FBX_Neck1.s" "FBX_Head.is";
connectAttr "SKELETON.di" "FBX_Head.do";
connectAttr "FBX_Head.s" "FBX_LeftEye.is";
connectAttr "SKELETON.di" "FBX_LeftEye.do";
connectAttr "FBX_Head.s" "FBX_RightEye.is";
connectAttr "SKELETON.di" "FBX_RightEye.do";
connectAttr "polyCube1.out" "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1.i"
		;
connectAttr "FBX_Neck.s" "FBX_NeckRoll.is";
connectAttr "SKELETON.di" "FBX_NeckRoll.do";
connectAttr "unitConversion14.o" "FBX_NeckRoll.rx";
connectAttr "FBX_Spine3.s" "FBX_LeftShoulder.is";
connectAttr "SKELETON.di" "FBX_LeftShoulder.do";
connectAttr "FBX_LeftShoulder.s" "FBX_LeftArm.is";
connectAttr "SKELETON.di" "FBX_LeftArm.do";
connectAttr "FBX_LeftArm.s" "FBX_LeftForeArm.is";
connectAttr "SKELETON.di" "FBX_LeftForeArm.do";
connectAttr "FBX_LeftForeArm.s" "FBX_LeftHand.is";
connectAttr "SKELETON.di" "FBX_LeftHand.do";
connectAttr "FBX_LeftHand.s" "FBX_LeftHandThumb1.is";
connectAttr "SKELETON.di" "FBX_LeftHandThumb1.do";
connectAttr "FBX_LeftHandThumb1.s" "FBX_LeftHandThumb2.is";
connectAttr "SKELETON.di" "FBX_LeftHandThumb2.do";
connectAttr "FBX_LeftHandThumb2.s" "FBX_LeftHandThumb3.is";
connectAttr "SKELETON.di" "FBX_LeftHandThumb3.do";
connectAttr "FBX_LeftHandThumb3.s" "FBX_LeftHandThumb4.is";
connectAttr "SKELETON.di" "FBX_LeftHandThumb4.do";
connectAttr "FBX_LeftHand.s" "FBX_LeftHandMiddle0.is";
connectAttr "SKELETON.di" "FBX_LeftHandMiddle0.do";
connectAttr "FBX_LeftHandMiddle0.s" "FBX_LeftHandMiddle1.is";
connectAttr "SKELETON.di" "FBX_LeftHandMiddle1.do";
connectAttr "FBX_LeftHandMiddle1.s" "FBX_LeftHandMiddle2.is";
connectAttr "SKELETON.di" "FBX_LeftHandMiddle2.do";
connectAttr "FBX_LeftHandMiddle2.s" "FBX_LeftHandMiddle3.is";
connectAttr "SKELETON.di" "FBX_LeftHandMiddle3.do";
connectAttr "FBX_LeftHandMiddle3.s" "FBX_LeftHandMiddle4.is";
connectAttr "SKELETON.di" "FBX_LeftHandMiddle4.do";
connectAttr "unitConversion34.o" "FBX_LeftHandRoll.rz";
connectAttr "FBX_LeftHand.s" "FBX_LeftHandRoll.is";
connectAttr "SKELETON.di" "FBX_LeftHandRoll.do";
connectAttr "unitConversion30.o" "FBX_LeftElbowRoll.ry";
connectAttr "FBX_LeftForeArm.s" "FBX_LeftElbowRoll.is";
connectAttr "SKELETON.di" "FBX_LeftElbowRoll.do";
connectAttr "FBX_LeftElbowRoll.s" "FBX_LeftElbowRoll_End.is";
connectAttr "SKELETON.di" "FBX_LeftElbowRoll_End.do";
connectAttr "FBX_LeftForeArm.s" "FBX_LeftForeArmRoll.is";
connectAttr "unitConversion20.o" "FBX_LeftForeArmRoll.rx";
connectAttr "SKELETON.di" "FBX_LeftForeArmRoll.do";
connectAttr "FBX_LeftForeArm.s" "FBX_LeftForeArmRoll1.is";
connectAttr "unitConversion21.o" "FBX_LeftForeArmRoll1.rx";
connectAttr "SKELETON.di" "FBX_LeftForeArmRoll1.do";
connectAttr "unitConversion16.o" "FBX_LeftArmRoll.rx";
connectAttr "FBX_LeftArm.s" "FBX_LeftArmRoll.is";
connectAttr "SKELETON.di" "FBX_LeftArmRoll.do";
connectAttr "FBX_Spine3.s" "FBX_RightShoulder.is";
connectAttr "SKELETON.di" "FBX_RightShoulder.do";
connectAttr "FBX_RightShoulder.s" "FBX_RightArm.is";
connectAttr "SKELETON.di" "FBX_RightArm.do";
connectAttr "FBX_RightArm.s" "FBX_RightForeArm.is";
connectAttr "SKELETON.di" "FBX_RightForeArm.do";
connectAttr "FBX_RightForeArm.s" "FBX_RightHand.is";
connectAttr "SKELETON.di" "FBX_RightHand.do";
connectAttr "FBX_RightHand.s" "FBX_RightHandThumb1.is";
connectAttr "SKELETON.di" "FBX_RightHandThumb1.do";
connectAttr "FBX_RightHandThumb1.s" "FBX_RightHandThumb2.is";
connectAttr "SKELETON.di" "FBX_RightHandThumb2.do";
connectAttr "FBX_RightHandThumb2.s" "FBX_RightHandThumb3.is";
connectAttr "SKELETON.di" "FBX_RightHandThumb3.do";
connectAttr "FBX_RightHandThumb3.s" "FBX_RightHandThumb4.is";
connectAttr "SKELETON.di" "FBX_RightHandThumb4.do";
connectAttr "FBX_RightHand.s" "FBX_RightHandMiddle0.is";
connectAttr "SKELETON.di" "FBX_RightHandMiddle0.do";
connectAttr "FBX_RightHandMiddle0.s" "FBX_RightHandMiddle1.is";
connectAttr "SKELETON.di" "FBX_RightHandMiddle1.do";
connectAttr "FBX_RightHandMiddle1.s" "FBX_RightHandMiddle2.is";
connectAttr "SKELETON.di" "FBX_RightHandMiddle2.do";
connectAttr "FBX_RightHandMiddle2.s" "FBX_RightHandMiddle3.is";
connectAttr "SKELETON.di" "FBX_RightHandMiddle3.do";
connectAttr "FBX_RightHandMiddle3.s" "FBX_RightHandMiddle4.is";
connectAttr "SKELETON.di" "FBX_RightHandMiddle4.do";
connectAttr "unitConversion36.o" "FBX_RightHandRoll.rz";
connectAttr "FBX_RightHand.s" "FBX_RightHandRoll.is";
connectAttr "SKELETON.di" "FBX_RightHandRoll.do";
connectAttr "unitConversion32.o" "FBX_RightElbowRoll.ry";
connectAttr "FBX_RightForeArm.s" "FBX_RightElbowRoll.is";
connectAttr "SKELETON.di" "FBX_RightElbowRoll.do";
connectAttr "FBX_RightElbowRoll.s" "FBX_RightElbowRoll_End.is";
connectAttr "SKELETON.di" "FBX_RightElbowRoll_End.do";
connectAttr "FBX_RightForeArm.s" "FBX_RightForeArmRoll.is";
connectAttr "unitConversion23.o" "FBX_RightForeArmRoll.rx";
connectAttr "SKELETON.di" "FBX_RightForeArmRoll.do";
connectAttr "FBX_RightForeArm.s" "FBX_RightForeArmRoll1.is";
connectAttr "unitConversion24.o" "FBX_RightForeArmRoll1.rx";
connectAttr "SKELETON.di" "FBX_RightForeArmRoll1.do";
connectAttr "unitConversion18.o" "FBX_RightArmRoll.rx";
connectAttr "FBX_RightArm.s" "FBX_RightArmRoll.is";
connectAttr "SKELETON.di" "FBX_RightArmRoll.do";
connectAttr "FBX_Hips.s" "FBX_LeftUpLeg.is";
connectAttr "SKELETON.di" "FBX_LeftUpLeg.do";
connectAttr "FBX_LeftUpLeg.s" "FBX_LeftLeg.is";
connectAttr "SKELETON.di" "FBX_LeftLeg.do";
connectAttr "FBX_LeftLeg.s" "FBX_LeftFoot.is";
connectAttr "SKELETON.di" "FBX_LeftFoot.do";
connectAttr "FBX_LeftFoot.s" "FBX_LeftToeBase.is";
connectAttr "SKELETON.di" "FBX_LeftToeBase.do";
connectAttr "FBX_LeftToeBase.s" "FBX_LeftToes_End.is";
connectAttr "SKELETON.di" "FBX_LeftToes_End.do";
connectAttr "unitConversion10.o" "FBX_LeftFootRoll.rx";
connectAttr "unitConversion12.o" "FBX_LeftFootRoll.rz";
connectAttr "FBX_LeftFoot.s" "FBX_LeftFootRoll.is";
connectAttr "SKELETON.di" "FBX_LeftFootRoll.do";
connectAttr "unitConversion28.o" "FBX_LeftKneeRoll.ry";
connectAttr "FBX_LeftLeg.s" "FBX_LeftKneeRoll.is";
connectAttr "SKELETON.di" "FBX_LeftKneeRoll.do";
connectAttr "FBX_LeftKneeRoll.s" "FBX_LeftKneeRoll_End.is";
connectAttr "SKELETON.di" "FBX_LeftKneeRoll_End.do";
connectAttr "FBX_LeftUpLeg.s" "FBX_LeftUpLegRoll.is";
connectAttr "SKELETON.di" "FBX_LeftUpLegRoll.do";
connectAttr "unitConversion4.o" "FBX_LeftUpLegRoll.rx";
connectAttr "FBX_Hips.s" "FBX_RightUpLeg.is";
connectAttr "SKELETON.di" "FBX_RightUpLeg.do";
connectAttr "FBX_RightUpLeg.s" "FBX_RightLeg.is";
connectAttr "SKELETON.di" "FBX_RightLeg.do";
connectAttr "FBX_RightLeg.s" "FBX_RightFoot.is";
connectAttr "SKELETON.di" "FBX_RightFoot.do";
connectAttr "FBX_RightFoot.s" "FBX_RightToeBase.is";
connectAttr "SKELETON.di" "FBX_RightToeBase.do";
connectAttr "FBX_RightToeBase.s" "FBX_RightToes_End.is";
connectAttr "SKELETON.di" "FBX_RightToes_End.do";
connectAttr "unitConversion6.o" "FBX_RightFootRoll.rx";
connectAttr "unitConversion8.o" "FBX_RightFootRoll.rz";
connectAttr "FBX_RightFoot.s" "FBX_RightFootRoll.is";
connectAttr "SKELETON.di" "FBX_RightFootRoll.do";
connectAttr "unitConversion26.o" "FBX_RightKneeRoll.ry";
connectAttr "FBX_RightLeg.s" "FBX_RightKneeRoll.is";
connectAttr "SKELETON.di" "FBX_RightKneeRoll.do";
connectAttr "FBX_RightKneeRoll.s" "FBX_RightKneeRoll_End.is";
connectAttr "SKELETON.di" "FBX_RightKneeRoll_End.do";
connectAttr "FBX_RightUpLeg.s" "FBX_RightUpLegRoll.is";
connectAttr "unitConversion2.o" "FBX_RightUpLegRoll.rx";
connectAttr "SKELETON.di" "FBX_RightUpLegRoll.do";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[5].sllk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.slnk[5].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[6].sllk";
connectAttr ":initialParticleSE.msg" "lightLinker1.slnk[6].solk";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "layerManager.dli[1]" "MODEL.id";
connectAttr "layerManager.dli[2]" "SKELETON.id";
connectAttr "FBX_Hips.msg" "FBX_AMFlexStance.m[3]";
connectAttr "FBX_Spine.msg" "FBX_AMFlexStance.m[4]";
connectAttr "FBX_Spine1.msg" "FBX_AMFlexStance.m[5]";
connectAttr "FBX_Spine2.msg" "FBX_AMFlexStance.m[6]";
connectAttr "FBX_Spine3.msg" "FBX_AMFlexStance.m[7]";
connectAttr "FBX_Neck.msg" "FBX_AMFlexStance.m[8]";
connectAttr "FBX_Neck1.msg" "FBX_AMFlexStance.m[9]";
connectAttr "FBX_Head.msg" "FBX_AMFlexStance.m[10]";
connectAttr "FBX_LeftShoulder.msg" "FBX_AMFlexStance.m[13]";
connectAttr "FBX_LeftArm.msg" "FBX_AMFlexStance.m[14]";
connectAttr "FBX_LeftArmRoll.msg" "FBX_AMFlexStance.m[15]";
connectAttr "FBX_LeftForeArm.msg" "FBX_AMFlexStance.m[16]";
connectAttr "FBX_LeftElbowRoll.msg" "FBX_AMFlexStance.m[17]";
connectAttr "FBX_LeftElbowRoll_End.msg" "FBX_AMFlexStance.m[18]";
connectAttr "FBX_LeftEye.msg" "FBX_AMFlexStance.m[19]";
connectAttr "FBX_LeftUpLeg.msg" "FBX_AMFlexStance.m[20]";
connectAttr "FBX_LeftLeg.msg" "FBX_AMFlexStance.m[21]";
connectAttr "FBX_LeftFoot.msg" "FBX_AMFlexStance.m[22]";
connectAttr "FBX_LeftFootRoll.msg" "FBX_AMFlexStance.m[23]";
connectAttr "FBX_LeftForeArmRoll.msg" "FBX_AMFlexStance.m[24]";
connectAttr "FBX_LeftForeArmRoll1.msg" "FBX_AMFlexStance.m[25]";
connectAttr "FBX_LeftHand.msg" "FBX_AMFlexStance.m[26]";
connectAttr "FBX_LeftHandMiddle0.msg" "FBX_AMFlexStance.m[27]";
connectAttr "FBX_LeftHandMiddle1.msg" "FBX_AMFlexStance.m[28]";
connectAttr "FBX_LeftHandMiddle2.msg" "FBX_AMFlexStance.m[29]";
connectAttr "FBX_LeftHandMiddle3.msg" "FBX_AMFlexStance.m[30]";
connectAttr "FBX_LeftHandMiddle4.msg" "FBX_AMFlexStance.m[31]";
connectAttr "FBX_LeftHandRoll.msg" "FBX_AMFlexStance.m[32]";
connectAttr "FBX_LeftHandThumb1.msg" "FBX_AMFlexStance.m[33]";
connectAttr "FBX_LeftHandThumb2.msg" "FBX_AMFlexStance.m[34]";
connectAttr "FBX_LeftHandThumb3.msg" "FBX_AMFlexStance.m[35]";
connectAttr "FBX_LeftHandThumb4.msg" "FBX_AMFlexStance.m[36]";
connectAttr "FBX_LeftKneeRoll.msg" "FBX_AMFlexStance.m[37]";
connectAttr "FBX_LeftKneeRoll_End.msg" "FBX_AMFlexStance.m[38]";
connectAttr "FBX_LeftToeBase.msg" "FBX_AMFlexStance.m[39]";
connectAttr "FBX_LeftToes_End.msg" "FBX_AMFlexStance.m[40]";
connectAttr "FBX_LeftUpLegRoll.msg" "FBX_AMFlexStance.m[41]";
connectAttr "FBX_NeckRoll.msg" "FBX_AMFlexStance.m[42]";
connectAttr "FBX_RightShoulder.msg" "FBX_AMFlexStance.m[43]";
connectAttr "FBX_RightArm.msg" "FBX_AMFlexStance.m[44]";
connectAttr "FBX_RightArmRoll.msg" "FBX_AMFlexStance.m[45]";
connectAttr "FBX_RightForeArm.msg" "FBX_AMFlexStance.m[46]";
connectAttr "FBX_RightElbowRoll.msg" "FBX_AMFlexStance.m[47]";
connectAttr "FBX_RightElbowRoll_End.msg" "FBX_AMFlexStance.m[48]";
connectAttr "FBX_RightEye.msg" "FBX_AMFlexStance.m[49]";
connectAttr "FBX_RightUpLeg.msg" "FBX_AMFlexStance.m[50]";
connectAttr "FBX_RightLeg.msg" "FBX_AMFlexStance.m[51]";
connectAttr "FBX_RightFoot.msg" "FBX_AMFlexStance.m[52]";
connectAttr "FBX_RightFootRoll.msg" "FBX_AMFlexStance.m[53]";
connectAttr "FBX_RightForeArmRoll.msg" "FBX_AMFlexStance.m[54]";
connectAttr "FBX_RightForeArmRoll1.msg" "FBX_AMFlexStance.m[55]";
connectAttr "FBX_RightHand.msg" "FBX_AMFlexStance.m[56]";
connectAttr "FBX_RightHandMiddle0.msg" "FBX_AMFlexStance.m[57]";
connectAttr "FBX_RightHandMiddle1.msg" "FBX_AMFlexStance.m[58]";
connectAttr "FBX_RightHandMiddle2.msg" "FBX_AMFlexStance.m[59]";
connectAttr "FBX_RightHandMiddle3.msg" "FBX_AMFlexStance.m[60]";
connectAttr "FBX_RightHandMiddle4.msg" "FBX_AMFlexStance.m[61]";
connectAttr "FBX_RightHandRoll.msg" "FBX_AMFlexStance.m[62]";
connectAttr "FBX_RightHandThumb1.msg" "FBX_AMFlexStance.m[63]";
connectAttr "FBX_RightHandThumb2.msg" "FBX_AMFlexStance.m[64]";
connectAttr "FBX_RightHandThumb3.msg" "FBX_AMFlexStance.m[65]";
connectAttr "FBX_RightHandThumb4.msg" "FBX_AMFlexStance.m[66]";
connectAttr "FBX_RightKneeRoll.msg" "FBX_AMFlexStance.m[67]";
connectAttr "FBX_RightKneeRoll_End.msg" "FBX_AMFlexStance.m[68]";
connectAttr "FBX_RightToeBase.msg" "FBX_AMFlexStance.m[69]";
connectAttr "FBX_RightToes_End.msg" "FBX_AMFlexStance.m[70]";
connectAttr "FBX_RightUpLegRoll.msg" "FBX_AMFlexStance.m[71]";
connectAttr "FBX_AMFlexStance.w" "FBX_AMFlexStance.p[0]";
connectAttr "FBX_AMFlexStance.m[0]" "FBX_AMFlexStance.p[1]";
connectAttr "FBX_AMFlexStance.m[1]" "FBX_AMFlexStance.p[2]";
connectAttr "FBX_AMFlexStance.m[2]" "FBX_AMFlexStance.p[3]";
connectAttr "FBX_AMFlexStance.m[3]" "FBX_AMFlexStance.p[4]";
connectAttr "FBX_AMFlexStance.m[4]" "FBX_AMFlexStance.p[5]";
connectAttr "FBX_AMFlexStance.m[5]" "FBX_AMFlexStance.p[6]";
connectAttr "FBX_AMFlexStance.m[6]" "FBX_AMFlexStance.p[7]";
connectAttr "FBX_AMFlexStance.m[7]" "FBX_AMFlexStance.p[8]";
connectAttr "FBX_AMFlexStance.m[8]" "FBX_AMFlexStance.p[9]";
connectAttr "FBX_AMFlexStance.m[9]" "FBX_AMFlexStance.p[10]";
connectAttr "FBX_AMFlexStance.m[10]" "FBX_AMFlexStance.p[11]";
connectAttr "FBX_AMFlexStance.m[10]" "FBX_AMFlexStance.p[12]";
connectAttr "FBX_AMFlexStance.m[7]" "FBX_AMFlexStance.p[13]";
connectAttr "FBX_AMFlexStance.m[13]" "FBX_AMFlexStance.p[14]";
connectAttr "FBX_AMFlexStance.m[14]" "FBX_AMFlexStance.p[15]";
connectAttr "FBX_AMFlexStance.m[14]" "FBX_AMFlexStance.p[16]";
connectAttr "FBX_AMFlexStance.m[16]" "FBX_AMFlexStance.p[17]";
connectAttr "FBX_AMFlexStance.m[17]" "FBX_AMFlexStance.p[18]";
connectAttr "FBX_AMFlexStance.m[10]" "FBX_AMFlexStance.p[19]";
connectAttr "FBX_AMFlexStance.m[3]" "FBX_AMFlexStance.p[20]";
connectAttr "FBX_AMFlexStance.m[20]" "FBX_AMFlexStance.p[21]";
connectAttr "FBX_AMFlexStance.m[21]" "FBX_AMFlexStance.p[22]";
connectAttr "FBX_AMFlexStance.m[22]" "FBX_AMFlexStance.p[23]";
connectAttr "FBX_AMFlexStance.m[16]" "FBX_AMFlexStance.p[24]";
connectAttr "FBX_AMFlexStance.m[16]" "FBX_AMFlexStance.p[25]";
connectAttr "FBX_AMFlexStance.m[16]" "FBX_AMFlexStance.p[26]";
connectAttr "FBX_AMFlexStance.m[26]" "FBX_AMFlexStance.p[27]";
connectAttr "FBX_AMFlexStance.m[27]" "FBX_AMFlexStance.p[28]";
connectAttr "FBX_AMFlexStance.m[28]" "FBX_AMFlexStance.p[29]";
connectAttr "FBX_AMFlexStance.m[29]" "FBX_AMFlexStance.p[30]";
connectAttr "FBX_AMFlexStance.m[30]" "FBX_AMFlexStance.p[31]";
connectAttr "FBX_AMFlexStance.m[26]" "FBX_AMFlexStance.p[32]";
connectAttr "FBX_AMFlexStance.m[26]" "FBX_AMFlexStance.p[33]";
connectAttr "FBX_AMFlexStance.m[33]" "FBX_AMFlexStance.p[34]";
connectAttr "FBX_AMFlexStance.m[34]" "FBX_AMFlexStance.p[35]";
connectAttr "FBX_AMFlexStance.m[35]" "FBX_AMFlexStance.p[36]";
connectAttr "FBX_AMFlexStance.m[21]" "FBX_AMFlexStance.p[37]";
connectAttr "FBX_AMFlexStance.m[37]" "FBX_AMFlexStance.p[38]";
connectAttr "FBX_AMFlexStance.m[22]" "FBX_AMFlexStance.p[39]";
connectAttr "FBX_AMFlexStance.m[39]" "FBX_AMFlexStance.p[40]";
connectAttr "FBX_AMFlexStance.m[20]" "FBX_AMFlexStance.p[41]";
connectAttr "FBX_AMFlexStance.m[8]" "FBX_AMFlexStance.p[42]";
connectAttr "FBX_AMFlexStance.m[7]" "FBX_AMFlexStance.p[43]";
connectAttr "FBX_AMFlexStance.m[43]" "FBX_AMFlexStance.p[44]";
connectAttr "FBX_AMFlexStance.m[44]" "FBX_AMFlexStance.p[45]";
connectAttr "FBX_AMFlexStance.m[44]" "FBX_AMFlexStance.p[46]";
connectAttr "FBX_AMFlexStance.m[46]" "FBX_AMFlexStance.p[47]";
connectAttr "FBX_AMFlexStance.m[47]" "FBX_AMFlexStance.p[48]";
connectAttr "FBX_AMFlexStance.m[10]" "FBX_AMFlexStance.p[49]";
connectAttr "FBX_AMFlexStance.m[3]" "FBX_AMFlexStance.p[50]";
connectAttr "FBX_AMFlexStance.m[50]" "FBX_AMFlexStance.p[51]";
connectAttr "FBX_AMFlexStance.m[51]" "FBX_AMFlexStance.p[52]";
connectAttr "FBX_AMFlexStance.m[52]" "FBX_AMFlexStance.p[53]";
connectAttr "FBX_AMFlexStance.m[46]" "FBX_AMFlexStance.p[54]";
connectAttr "FBX_AMFlexStance.m[46]" "FBX_AMFlexStance.p[55]";
connectAttr "FBX_AMFlexStance.m[46]" "FBX_AMFlexStance.p[56]";
connectAttr "FBX_AMFlexStance.m[56]" "FBX_AMFlexStance.p[57]";
connectAttr "FBX_AMFlexStance.m[57]" "FBX_AMFlexStance.p[58]";
connectAttr "FBX_AMFlexStance.m[58]" "FBX_AMFlexStance.p[59]";
connectAttr "FBX_AMFlexStance.m[59]" "FBX_AMFlexStance.p[60]";
connectAttr "FBX_AMFlexStance.m[60]" "FBX_AMFlexStance.p[61]";
connectAttr "FBX_AMFlexStance.m[56]" "FBX_AMFlexStance.p[62]";
connectAttr "FBX_AMFlexStance.m[56]" "FBX_AMFlexStance.p[63]";
connectAttr "FBX_AMFlexStance.m[63]" "FBX_AMFlexStance.p[64]";
connectAttr "FBX_AMFlexStance.m[64]" "FBX_AMFlexStance.p[65]";
connectAttr "FBX_AMFlexStance.m[65]" "FBX_AMFlexStance.p[66]";
connectAttr "FBX_AMFlexStance.m[51]" "FBX_AMFlexStance.p[67]";
connectAttr "FBX_AMFlexStance.m[67]" "FBX_AMFlexStance.p[68]";
connectAttr "FBX_AMFlexStance.m[52]" "FBX_AMFlexStance.p[69]";
connectAttr "FBX_AMFlexStance.m[69]" "FBX_AMFlexStance.p[70]";
connectAttr "FBX_AMFlexStance.m[50]" "FBX_AMFlexStance.p[71]";
connectAttr "FBX_AMFlexStance.m[12]" "FBX_AMFlexStance.p[72]";
connectAttr "FBX_AMFlexStance.m[72]" "FBX_AMFlexStance.p[73]";
connectAttr "FBX_AMFlexStance.m[73]" "FBX_AMFlexStance.p[74]";
connectAttr "FBX_AMFlexStance.m[74]" "FBX_AMFlexStance.p[75]";
connectAttr "FBX_AMFlexStance.m[11]" "FBX_AMFlexStance.p[76]";
connectAttr "FBX_AMFlexStance.m[76]" "FBX_AMFlexStance.p[77]";
connectAttr "FBX_AMFlexStance.m[77]" "FBX_AMFlexStance.p[78]";
connectAttr "FBX_AMFlexStance.m[78]" "FBX_AMFlexStance.p[79]";
connectAttr "FBX_AMFlexStance.m[79]" "FBX_AMFlexStance.p[80]";
connectAttr "FBX_AMFlexStance.m[80]" "FBX_AMFlexStance.p[81]";
connectAttr "FBX_AMFlexStance.m[81]" "FBX_AMFlexStance.p[82]";
connectAttr "FBX_AMFlexStance.m[82]" "FBX_AMFlexStance.p[83]";
connectAttr "FBX_AMFlexStance.m[83]" "FBX_AMFlexStance.p[84]";
connectAttr "FBX_AMFlexStance.m[84]" "FBX_AMFlexStance.p[85]";
connectAttr "FBX_AMFlexStance.m[85]" "FBX_AMFlexStance.p[86]";
connectAttr "FBX_AMFlexStance.m[86]" "FBX_AMFlexStance.p[87]";
connectAttr "FBX_AMFlexStance.m[11]" "FBX_AMFlexStance.p[88]";
connectAttr "FBX_AMFlexStance.m[88]" "FBX_AMFlexStance.p[89]";
connectAttr "FBX_AMFlexStance.m[89]" "FBX_AMFlexStance.p[90]";
connectAttr "FBX_AMFlexStance.m[90]" "FBX_AMFlexStance.p[91]";
connectAttr "FBX_AMFlexStance.m[91]" "FBX_AMFlexStance.p[92]";
connectAttr "FBX_AMFlexStance.m[92]" "FBX_AMFlexStance.p[93]";
connectAttr "FBX_AMFlexStance.m[93]" "FBX_AMFlexStance.p[94]";
connectAttr "FBX_AMFlexStance.m[94]" "FBX_AMFlexStance.p[95]";
connectAttr "FBX_AMFlexStance.m[95]" "FBX_AMFlexStance.p[96]";
connectAttr "FBX_AMFlexStance.m[96]" "FBX_AMFlexStance.p[97]";
connectAttr "FBX_AMFlexStance.m[97]" "FBX_AMFlexStance.p[98]";
connectAttr "FBX_AMFlexStance.m[98]" "FBX_AMFlexStance.p[99]";
connectAttr "FBX_Hips.msg" "FBX_AMTStance.m[3]";
connectAttr "FBX_Spine.msg" "FBX_AMTStance.m[4]";
connectAttr "FBX_Spine1.msg" "FBX_AMTStance.m[5]";
connectAttr "FBX_Spine2.msg" "FBX_AMTStance.m[6]";
connectAttr "FBX_Spine3.msg" "FBX_AMTStance.m[7]";
connectAttr "FBX_Neck.msg" "FBX_AMTStance.m[8]";
connectAttr "FBX_Neck1.msg" "FBX_AMTStance.m[9]";
connectAttr "FBX_Head.msg" "FBX_AMTStance.m[10]";
connectAttr "FBX_LeftShoulder.msg" "FBX_AMTStance.m[13]";
connectAttr "FBX_LeftArm.msg" "FBX_AMTStance.m[14]";
connectAttr "FBX_LeftArmRoll.msg" "FBX_AMTStance.m[15]";
connectAttr "FBX_LeftForeArm.msg" "FBX_AMTStance.m[16]";
connectAttr "FBX_LeftElbowRoll.msg" "FBX_AMTStance.m[17]";
connectAttr "FBX_LeftElbowRoll_End.msg" "FBX_AMTStance.m[18]";
connectAttr "FBX_LeftEye.msg" "FBX_AMTStance.m[19]";
connectAttr "FBX_LeftUpLeg.msg" "FBX_AMTStance.m[20]";
connectAttr "FBX_LeftLeg.msg" "FBX_AMTStance.m[21]";
connectAttr "FBX_LeftFoot.msg" "FBX_AMTStance.m[22]";
connectAttr "FBX_LeftFootRoll.msg" "FBX_AMTStance.m[23]";
connectAttr "FBX_LeftForeArmRoll.msg" "FBX_AMTStance.m[24]";
connectAttr "FBX_LeftForeArmRoll1.msg" "FBX_AMTStance.m[25]";
connectAttr "FBX_LeftHand.msg" "FBX_AMTStance.m[26]";
connectAttr "FBX_LeftHandMiddle0.msg" "FBX_AMTStance.m[27]";
connectAttr "FBX_LeftHandMiddle1.msg" "FBX_AMTStance.m[28]";
connectAttr "FBX_LeftHandMiddle2.msg" "FBX_AMTStance.m[29]";
connectAttr "FBX_LeftHandMiddle3.msg" "FBX_AMTStance.m[30]";
connectAttr "FBX_LeftHandMiddle4.msg" "FBX_AMTStance.m[31]";
connectAttr "FBX_LeftHandRoll.msg" "FBX_AMTStance.m[32]";
connectAttr "FBX_LeftHandThumb1.msg" "FBX_AMTStance.m[33]";
connectAttr "FBX_LeftHandThumb2.msg" "FBX_AMTStance.m[34]";
connectAttr "FBX_LeftHandThumb3.msg" "FBX_AMTStance.m[35]";
connectAttr "FBX_LeftHandThumb4.msg" "FBX_AMTStance.m[36]";
connectAttr "FBX_LeftKneeRoll.msg" "FBX_AMTStance.m[37]";
connectAttr "FBX_LeftKneeRoll_End.msg" "FBX_AMTStance.m[38]";
connectAttr "FBX_LeftToeBase.msg" "FBX_AMTStance.m[39]";
connectAttr "FBX_LeftToes_End.msg" "FBX_AMTStance.m[40]";
connectAttr "FBX_LeftUpLegRoll.msg" "FBX_AMTStance.m[41]";
connectAttr "FBX_NeckRoll.msg" "FBX_AMTStance.m[42]";
connectAttr "FBX_RightShoulder.msg" "FBX_AMTStance.m[43]";
connectAttr "FBX_RightArm.msg" "FBX_AMTStance.m[44]";
connectAttr "FBX_RightArmRoll.msg" "FBX_AMTStance.m[45]";
connectAttr "FBX_RightForeArm.msg" "FBX_AMTStance.m[46]";
connectAttr "FBX_RightElbowRoll.msg" "FBX_AMTStance.m[47]";
connectAttr "FBX_RightElbowRoll_End.msg" "FBX_AMTStance.m[48]";
connectAttr "FBX_RightEye.msg" "FBX_AMTStance.m[49]";
connectAttr "FBX_RightUpLeg.msg" "FBX_AMTStance.m[50]";
connectAttr "FBX_RightLeg.msg" "FBX_AMTStance.m[51]";
connectAttr "FBX_RightFoot.msg" "FBX_AMTStance.m[52]";
connectAttr "FBX_RightFootRoll.msg" "FBX_AMTStance.m[53]";
connectAttr "FBX_RightForeArmRoll.msg" "FBX_AMTStance.m[54]";
connectAttr "FBX_RightForeArmRoll1.msg" "FBX_AMTStance.m[55]";
connectAttr "FBX_RightHand.msg" "FBX_AMTStance.m[56]";
connectAttr "FBX_RightHandMiddle0.msg" "FBX_AMTStance.m[57]";
connectAttr "FBX_RightHandMiddle1.msg" "FBX_AMTStance.m[58]";
connectAttr "FBX_RightHandMiddle2.msg" "FBX_AMTStance.m[59]";
connectAttr "FBX_RightHandMiddle3.msg" "FBX_AMTStance.m[60]";
connectAttr "FBX_RightHandMiddle4.msg" "FBX_AMTStance.m[61]";
connectAttr "FBX_RightHandRoll.msg" "FBX_AMTStance.m[62]";
connectAttr "FBX_RightHandThumb1.msg" "FBX_AMTStance.m[63]";
connectAttr "FBX_RightHandThumb2.msg" "FBX_AMTStance.m[64]";
connectAttr "FBX_RightHandThumb3.msg" "FBX_AMTStance.m[65]";
connectAttr "FBX_RightHandThumb4.msg" "FBX_AMTStance.m[66]";
connectAttr "FBX_RightKneeRoll.msg" "FBX_AMTStance.m[67]";
connectAttr "FBX_RightKneeRoll_End.msg" "FBX_AMTStance.m[68]";
connectAttr "FBX_RightToeBase.msg" "FBX_AMTStance.m[69]";
connectAttr "FBX_RightToes_End.msg" "FBX_AMTStance.m[70]";
connectAttr "FBX_RightUpLegRoll.msg" "FBX_AMTStance.m[71]";
connectAttr "FBX_AMTStance.w" "FBX_AMTStance.p[0]";
connectAttr "FBX_AMTStance.m[0]" "FBX_AMTStance.p[1]";
connectAttr "FBX_AMTStance.m[1]" "FBX_AMTStance.p[2]";
connectAttr "FBX_AMTStance.m[2]" "FBX_AMTStance.p[3]";
connectAttr "FBX_AMTStance.m[3]" "FBX_AMTStance.p[4]";
connectAttr "FBX_AMTStance.m[4]" "FBX_AMTStance.p[5]";
connectAttr "FBX_AMTStance.m[5]" "FBX_AMTStance.p[6]";
connectAttr "FBX_AMTStance.m[6]" "FBX_AMTStance.p[7]";
connectAttr "FBX_AMTStance.m[7]" "FBX_AMTStance.p[8]";
connectAttr "FBX_AMTStance.m[8]" "FBX_AMTStance.p[9]";
connectAttr "FBX_AMTStance.m[9]" "FBX_AMTStance.p[10]";
connectAttr "FBX_AMTStance.m[10]" "FBX_AMTStance.p[11]";
connectAttr "FBX_AMTStance.m[10]" "FBX_AMTStance.p[12]";
connectAttr "FBX_AMTStance.m[7]" "FBX_AMTStance.p[13]";
connectAttr "FBX_AMTStance.m[13]" "FBX_AMTStance.p[14]";
connectAttr "FBX_AMTStance.m[14]" "FBX_AMTStance.p[15]";
connectAttr "FBX_AMTStance.m[14]" "FBX_AMTStance.p[16]";
connectAttr "FBX_AMTStance.m[16]" "FBX_AMTStance.p[17]";
connectAttr "FBX_AMTStance.m[17]" "FBX_AMTStance.p[18]";
connectAttr "FBX_AMTStance.m[10]" "FBX_AMTStance.p[19]";
connectAttr "FBX_AMTStance.m[3]" "FBX_AMTStance.p[20]";
connectAttr "FBX_AMTStance.m[20]" "FBX_AMTStance.p[21]";
connectAttr "FBX_AMTStance.m[21]" "FBX_AMTStance.p[22]";
connectAttr "FBX_AMTStance.m[22]" "FBX_AMTStance.p[23]";
connectAttr "FBX_AMTStance.m[16]" "FBX_AMTStance.p[24]";
connectAttr "FBX_AMTStance.m[16]" "FBX_AMTStance.p[25]";
connectAttr "FBX_AMTStance.m[16]" "FBX_AMTStance.p[26]";
connectAttr "FBX_AMTStance.m[26]" "FBX_AMTStance.p[27]";
connectAttr "FBX_AMTStance.m[27]" "FBX_AMTStance.p[28]";
connectAttr "FBX_AMTStance.m[28]" "FBX_AMTStance.p[29]";
connectAttr "FBX_AMTStance.m[29]" "FBX_AMTStance.p[30]";
connectAttr "FBX_AMTStance.m[30]" "FBX_AMTStance.p[31]";
connectAttr "FBX_AMTStance.m[26]" "FBX_AMTStance.p[32]";
connectAttr "FBX_AMTStance.m[26]" "FBX_AMTStance.p[33]";
connectAttr "FBX_AMTStance.m[33]" "FBX_AMTStance.p[34]";
connectAttr "FBX_AMTStance.m[34]" "FBX_AMTStance.p[35]";
connectAttr "FBX_AMTStance.m[35]" "FBX_AMTStance.p[36]";
connectAttr "FBX_AMTStance.m[21]" "FBX_AMTStance.p[37]";
connectAttr "FBX_AMTStance.m[37]" "FBX_AMTStance.p[38]";
connectAttr "FBX_AMTStance.m[22]" "FBX_AMTStance.p[39]";
connectAttr "FBX_AMTStance.m[39]" "FBX_AMTStance.p[40]";
connectAttr "FBX_AMTStance.m[20]" "FBX_AMTStance.p[41]";
connectAttr "FBX_AMTStance.m[8]" "FBX_AMTStance.p[42]";
connectAttr "FBX_AMTStance.m[7]" "FBX_AMTStance.p[43]";
connectAttr "FBX_AMTStance.m[43]" "FBX_AMTStance.p[44]";
connectAttr "FBX_AMTStance.m[44]" "FBX_AMTStance.p[45]";
connectAttr "FBX_AMTStance.m[44]" "FBX_AMTStance.p[46]";
connectAttr "FBX_AMTStance.m[46]" "FBX_AMTStance.p[47]";
connectAttr "FBX_AMTStance.m[47]" "FBX_AMTStance.p[48]";
connectAttr "FBX_AMTStance.m[10]" "FBX_AMTStance.p[49]";
connectAttr "FBX_AMTStance.m[3]" "FBX_AMTStance.p[50]";
connectAttr "FBX_AMTStance.m[50]" "FBX_AMTStance.p[51]";
connectAttr "FBX_AMTStance.m[51]" "FBX_AMTStance.p[52]";
connectAttr "FBX_AMTStance.m[52]" "FBX_AMTStance.p[53]";
connectAttr "FBX_AMTStance.m[46]" "FBX_AMTStance.p[54]";
connectAttr "FBX_AMTStance.m[46]" "FBX_AMTStance.p[55]";
connectAttr "FBX_AMTStance.m[46]" "FBX_AMTStance.p[56]";
connectAttr "FBX_AMTStance.m[56]" "FBX_AMTStance.p[57]";
connectAttr "FBX_AMTStance.m[57]" "FBX_AMTStance.p[58]";
connectAttr "FBX_AMTStance.m[58]" "FBX_AMTStance.p[59]";
connectAttr "FBX_AMTStance.m[59]" "FBX_AMTStance.p[60]";
connectAttr "FBX_AMTStance.m[60]" "FBX_AMTStance.p[61]";
connectAttr "FBX_AMTStance.m[56]" "FBX_AMTStance.p[62]";
connectAttr "FBX_AMTStance.m[56]" "FBX_AMTStance.p[63]";
connectAttr "FBX_AMTStance.m[63]" "FBX_AMTStance.p[64]";
connectAttr "FBX_AMTStance.m[64]" "FBX_AMTStance.p[65]";
connectAttr "FBX_AMTStance.m[65]" "FBX_AMTStance.p[66]";
connectAttr "FBX_AMTStance.m[51]" "FBX_AMTStance.p[67]";
connectAttr "FBX_AMTStance.m[67]" "FBX_AMTStance.p[68]";
connectAttr "FBX_AMTStance.m[52]" "FBX_AMTStance.p[69]";
connectAttr "FBX_AMTStance.m[69]" "FBX_AMTStance.p[70]";
connectAttr "FBX_AMTStance.m[50]" "FBX_AMTStance.p[71]";
connectAttr "FBX_AMTStance.m[12]" "FBX_AMTStance.p[72]";
connectAttr "FBX_AMTStance.m[72]" "FBX_AMTStance.p[73]";
connectAttr "FBX_AMTStance.m[73]" "FBX_AMTStance.p[74]";
connectAttr "FBX_AMTStance.m[74]" "FBX_AMTStance.p[75]";
connectAttr "FBX_AMTStance.m[11]" "FBX_AMTStance.p[76]";
connectAttr "FBX_AMTStance.m[76]" "FBX_AMTStance.p[77]";
connectAttr "FBX_AMTStance.m[77]" "FBX_AMTStance.p[78]";
connectAttr "FBX_AMTStance.m[78]" "FBX_AMTStance.p[79]";
connectAttr "FBX_AMTStance.m[79]" "FBX_AMTStance.p[80]";
connectAttr "FBX_AMTStance.m[80]" "FBX_AMTStance.p[81]";
connectAttr "FBX_AMTStance.m[81]" "FBX_AMTStance.p[82]";
connectAttr "FBX_AMTStance.m[82]" "FBX_AMTStance.p[83]";
connectAttr "FBX_AMTStance.m[83]" "FBX_AMTStance.p[84]";
connectAttr "FBX_AMTStance.m[84]" "FBX_AMTStance.p[85]";
connectAttr "FBX_AMTStance.m[85]" "FBX_AMTStance.p[86]";
connectAttr "FBX_AMTStance.m[86]" "FBX_AMTStance.p[87]";
connectAttr "FBX_AMTStance.m[11]" "FBX_AMTStance.p[88]";
connectAttr "FBX_AMTStance.m[88]" "FBX_AMTStance.p[89]";
connectAttr "FBX_AMTStance.m[89]" "FBX_AMTStance.p[90]";
connectAttr "FBX_AMTStance.m[90]" "FBX_AMTStance.p[91]";
connectAttr "FBX_AMTStance.m[91]" "FBX_AMTStance.p[92]";
connectAttr "FBX_AMTStance.m[92]" "FBX_AMTStance.p[93]";
connectAttr "FBX_AMTStance.m[93]" "FBX_AMTStance.p[94]";
connectAttr "FBX_AMTStance.m[94]" "FBX_AMTStance.p[95]";
connectAttr "FBX_AMTStance.m[95]" "FBX_AMTStance.p[96]";
connectAttr "FBX_AMTStance.m[96]" "FBX_AMTStance.p[97]";
connectAttr "FBX_AMTStance.m[97]" "FBX_AMTStance.p[98]";
connectAttr "FBX_AMTStance.m[98]" "FBX_AMTStance.p[99]";
connectAttr "unitConversion1.o" "ROOL_expr.in[1]";
connectAttr "unitConversion3.o" "ROOL_expr.in[3]";
connectAttr "unitConversion5.o" "ROOL_expr.in[5]";
connectAttr "unitConversion7.o" "ROOL_expr.in[6]";
connectAttr "unitConversion9.o" "ROOL_expr.in[8]";
connectAttr "unitConversion11.o" "ROOL_expr.in[9]";
connectAttr "unitConversion13.o" "ROOL_expr.in[11]";
connectAttr "unitConversion15.o" "ROOL_expr.in[13]";
connectAttr "unitConversion17.o" "ROOL_expr.in[15]";
connectAttr "unitConversion19.o" "ROOL_expr.in[17]";
connectAttr "unitConversion22.o" "ROOL_expr.in[20]";
connectAttr "unitConversion25.o" "ROOL_expr.in[23]";
connectAttr "unitConversion27.o" "ROOL_expr.in[25]";
connectAttr "unitConversion29.o" "ROOL_expr.in[27]";
connectAttr "unitConversion31.o" "ROOL_expr.in[29]";
connectAttr "unitConversion33.o" "ROOL_expr.in[31]";
connectAttr "unitConversion35.o" "ROOL_expr.in[33]";
connectAttr ":time1.o" "ROOL_expr.tim";
connectAttr "FBX_RightUpLeg.rx" "unitConversion1.i";
connectAttr "ROOL_expr.out[0]" "unitConversion2.i";
connectAttr "FBX_LeftUpLeg.rx" "unitConversion3.i";
connectAttr "ROOL_expr.out[1]" "unitConversion4.i";
connectAttr "FBX_RightFoot.rx" "unitConversion5.i";
connectAttr "ROOL_expr.out[2]" "unitConversion6.i";
connectAttr "FBX_RightFoot.rz" "unitConversion7.i";
connectAttr "ROOL_expr.out[3]" "unitConversion8.i";
connectAttr "FBX_LeftFoot.rx" "unitConversion9.i";
connectAttr "ROOL_expr.out[4]" "unitConversion10.i";
connectAttr "FBX_LeftFoot.rz" "unitConversion11.i";
connectAttr "ROOL_expr.out[5]" "unitConversion12.i";
connectAttr "FBX_Neck.rx" "unitConversion13.i";
connectAttr "ROOL_expr.out[6]" "unitConversion14.i";
connectAttr "FBX_LeftArm.rx" "unitConversion15.i";
connectAttr "ROOL_expr.out[7]" "unitConversion16.i";
connectAttr "FBX_RightArm.rx" "unitConversion17.i";
connectAttr "ROOL_expr.out[8]" "unitConversion18.i";
connectAttr "FBX_LeftHand.rx" "unitConversion19.i";
connectAttr "ROOL_expr.out[9]" "unitConversion20.i";
connectAttr "ROOL_expr.out[10]" "unitConversion21.i";
connectAttr "FBX_RightHand.rx" "unitConversion22.i";
connectAttr "ROOL_expr.out[11]" "unitConversion23.i";
connectAttr "ROOL_expr.out[12]" "unitConversion24.i";
connectAttr "FBX_RightLeg.ry" "unitConversion25.i";
connectAttr "ROOL_expr.out[13]" "unitConversion26.i";
connectAttr "FBX_LeftLeg.ry" "unitConversion27.i";
connectAttr "ROOL_expr.out[14]" "unitConversion28.i";
connectAttr "FBX_LeftForeArm.ry" "unitConversion29.i";
connectAttr "ROOL_expr.out[15]" "unitConversion30.i";
connectAttr "FBX_RightForeArm.ry" "unitConversion31.i";
connectAttr "ROOL_expr.out[16]" "unitConversion32.i";
connectAttr "FBX_LeftHand.rz" "unitConversion33.i";
connectAttr "ROOL_expr.out[17]" "unitConversion34.i";
connectAttr "FBX_RightHand.rz" "unitConversion35.i";
connectAttr "ROOL_expr.out[18]" "unitConversion36.i";
connectAttr "FBX_Hips.msg" "bindPose1.m[34]";
connectAttr "FBX_Spine.msg" "bindPose1.m[35]";
connectAttr "FBX_Spine1.msg" "bindPose1.m[36]";
connectAttr "FBX_Spine2.msg" "bindPose1.m[37]";
connectAttr "FBX_Spine3.msg" "bindPose1.m[38]";
connectAttr "FBX_Neck.msg" "bindPose1.m[39]";
connectAttr "FBX_Neck1.msg" "bindPose1.m[40]";
connectAttr "FBX_Head.msg" "bindPose1.m[41]";
connectAttr "FBX_LeftEye.msg" "bindPose1.m[67]";
connectAttr "FBX_RightEye.msg" "bindPose1.m[68]";
connectAttr "FBX_NeckRoll.msg" "bindPose1.m[74]";
connectAttr "FBX_LeftShoulder.msg" "bindPose1.m[75]";
connectAttr "FBX_LeftArm.msg" "bindPose1.m[76]";
connectAttr "FBX_LeftForeArm.msg" "bindPose1.m[77]";
connectAttr "FBX_LeftHand.msg" "bindPose1.m[78]";
connectAttr "FBX_LeftHandThumb1.msg" "bindPose1.m[79]";
connectAttr "FBX_LeftHandThumb2.msg" "bindPose1.m[80]";
connectAttr "FBX_LeftHandThumb3.msg" "bindPose1.m[81]";
connectAttr "FBX_LeftHandThumb4.msg" "bindPose1.m[82]";
connectAttr "FBX_LeftHandMiddle0.msg" "bindPose1.m[83]";
connectAttr "FBX_LeftHandMiddle1.msg" "bindPose1.m[84]";
connectAttr "FBX_LeftHandMiddle2.msg" "bindPose1.m[85]";
connectAttr "FBX_LeftHandMiddle3.msg" "bindPose1.m[86]";
connectAttr "FBX_LeftHandMiddle4.msg" "bindPose1.m[87]";
connectAttr "FBX_LeftHandRoll.msg" "bindPose1.m[88]";
connectAttr "FBX_LeftElbowRoll.msg" "bindPose1.m[89]";
connectAttr "FBX_LeftElbowRoll_End.msg" "bindPose1.m[90]";
connectAttr "FBX_LeftForeArmRoll.msg" "bindPose1.m[91]";
connectAttr "FBX_LeftForeArmRoll1.msg" "bindPose1.m[92]";
connectAttr "FBX_LeftArmRoll.msg" "bindPose1.m[93]";
connectAttr "FBX_RightShoulder.msg" "bindPose1.m[94]";
connectAttr "FBX_RightArm.msg" "bindPose1.m[95]";
connectAttr "FBX_RightForeArm.msg" "bindPose1.m[96]";
connectAttr "FBX_RightHand.msg" "bindPose1.m[97]";
connectAttr "FBX_RightHandThumb1.msg" "bindPose1.m[98]";
connectAttr "FBX_RightHandThumb2.msg" "bindPose1.m[99]";
connectAttr "FBX_RightHandThumb3.msg" "bindPose1.m[100]";
connectAttr "FBX_RightHandThumb4.msg" "bindPose1.m[101]";
connectAttr "FBX_RightHandMiddle0.msg" "bindPose1.m[102]";
connectAttr "FBX_RightHandMiddle1.msg" "bindPose1.m[103]";
connectAttr "FBX_RightHandMiddle2.msg" "bindPose1.m[104]";
connectAttr "FBX_RightHandMiddle3.msg" "bindPose1.m[105]";
connectAttr "FBX_RightHandMiddle4.msg" "bindPose1.m[106]";
connectAttr "FBX_RightHandRoll.msg" "bindPose1.m[107]";
connectAttr "FBX_RightElbowRoll.msg" "bindPose1.m[108]";
connectAttr "FBX_RightElbowRoll_End.msg" "bindPose1.m[109]";
connectAttr "FBX_RightForeArmRoll.msg" "bindPose1.m[110]";
connectAttr "FBX_RightForeArmRoll1.msg" "bindPose1.m[111]";
connectAttr "FBX_RightArmRoll.msg" "bindPose1.m[112]";
connectAttr "FBX_LeftUpLeg.msg" "bindPose1.m[113]";
connectAttr "FBX_LeftLeg.msg" "bindPose1.m[114]";
connectAttr "FBX_LeftFoot.msg" "bindPose1.m[115]";
connectAttr "FBX_LeftToeBase.msg" "bindPose1.m[116]";
connectAttr "FBX_LeftToes_End.msg" "bindPose1.m[117]";
connectAttr "FBX_LeftFootRoll.msg" "bindPose1.m[118]";
connectAttr "FBX_LeftKneeRoll.msg" "bindPose1.m[119]";
connectAttr "FBX_LeftKneeRoll_End.msg" "bindPose1.m[120]";
connectAttr "FBX_LeftUpLegRoll.msg" "bindPose1.m[121]";
connectAttr "FBX_RightUpLeg.msg" "bindPose1.m[122]";
connectAttr "FBX_RightLeg.msg" "bindPose1.m[123]";
connectAttr "FBX_RightFoot.msg" "bindPose1.m[124]";
connectAttr "FBX_RightToeBase.msg" "bindPose1.m[125]";
connectAttr "FBX_RightToes_End.msg" "bindPose1.m[126]";
connectAttr "FBX_RightFootRoll.msg" "bindPose1.m[127]";
connectAttr "FBX_RightKneeRoll.msg" "bindPose1.m[128]";
connectAttr "FBX_RightKneeRoll_End.msg" "bindPose1.m[129]";
connectAttr "FBX_RightUpLegRoll.msg" "bindPose1.m[130]";
connectAttr "bindPose1.w" "bindPose1.p[0]";
connectAttr "bindPose1.m[0]" "bindPose1.p[1]";
connectAttr "bindPose1.m[1]" "bindPose1.p[2]";
connectAttr "bindPose1.m[2]" "bindPose1.p[3]";
connectAttr "bindPose1.m[3]" "bindPose1.p[4]";
connectAttr "bindPose1.m[2]" "bindPose1.p[5]";
connectAttr "bindPose1.m[5]" "bindPose1.p[6]";
connectAttr "bindPose1.m[5]" "bindPose1.p[7]";
connectAttr "bindPose1.m[5]" "bindPose1.p[8]";
connectAttr "bindPose1.m[2]" "bindPose1.p[9]";
connectAttr "bindPose1.m[9]" "bindPose1.p[10]";
connectAttr "bindPose1.m[2]" "bindPose1.p[11]";
connectAttr "bindPose1.m[11]" "bindPose1.p[12]";
connectAttr "bindPose1.m[12]" "bindPose1.p[13]";
connectAttr "bindPose1.m[13]" "bindPose1.p[14]";
connectAttr "bindPose1.m[14]" "bindPose1.p[15]";
connectAttr "bindPose1.m[15]" "bindPose1.p[16]";
connectAttr "bindPose1.m[15]" "bindPose1.p[17]";
connectAttr "bindPose1.m[14]" "bindPose1.p[18]";
connectAttr "bindPose1.m[14]" "bindPose1.p[19]";
connectAttr "bindPose1.m[12]" "bindPose1.p[20]";
connectAttr "bindPose1.m[20]" "bindPose1.p[21]";
connectAttr "bindPose1.m[21]" "bindPose1.p[22]";
connectAttr "bindPose1.m[22]" "bindPose1.p[23]";
connectAttr "bindPose1.m[23]" "bindPose1.p[24]";
connectAttr "bindPose1.m[23]" "bindPose1.p[25]";
connectAttr "bindPose1.m[21]" "bindPose1.p[26]";
connectAttr "bindPose1.m[21]" "bindPose1.p[27]";
connectAttr "bindPose1.m[11]" "bindPose1.p[28]";
connectAttr "bindPose1.m[2]" "bindPose1.p[29]";
connectAttr "bindPose1.m[29]" "bindPose1.p[30]";
connectAttr "bindPose1.m[29]" "bindPose1.p[31]";
connectAttr "bindPose1.m[0]" "bindPose1.p[32]";
connectAttr "bindPose1.m[32]" "bindPose1.p[33]";
connectAttr "bindPose1.m[33]" "bindPose1.p[34]";
connectAttr "bindPose1.m[34]" "bindPose1.p[35]";
connectAttr "bindPose1.m[35]" "bindPose1.p[36]";
connectAttr "bindPose1.m[36]" "bindPose1.p[37]";
connectAttr "bindPose1.m[37]" "bindPose1.p[38]";
connectAttr "bindPose1.m[38]" "bindPose1.p[39]";
connectAttr "bindPose1.m[39]" "bindPose1.p[40]";
connectAttr "bindPose1.m[40]" "bindPose1.p[41]";
connectAttr "bindPose1.m[41]" "bindPose1.p[42]";
connectAttr "bindPose1.m[42]" "bindPose1.p[43]";
connectAttr "bindPose1.m[43]" "bindPose1.p[44]";
connectAttr "bindPose1.m[44]" "bindPose1.p[45]";
connectAttr "bindPose1.m[45]" "bindPose1.p[46]";
connectAttr "bindPose1.m[46]" "bindPose1.p[47]";
connectAttr "bindPose1.m[47]" "bindPose1.p[48]";
connectAttr "bindPose1.m[48]" "bindPose1.p[49]";
connectAttr "bindPose1.m[49]" "bindPose1.p[50]";
connectAttr "bindPose1.m[50]" "bindPose1.p[51]";
connectAttr "bindPose1.m[51]" "bindPose1.p[52]";
connectAttr "bindPose1.m[52]" "bindPose1.p[53]";
connectAttr "bindPose1.m[53]" "bindPose1.p[54]";
connectAttr "bindPose1.m[42]" "bindPose1.p[55]";
connectAttr "bindPose1.m[55]" "bindPose1.p[56]";
connectAttr "bindPose1.m[56]" "bindPose1.p[57]";
connectAttr "bindPose1.m[57]" "bindPose1.p[58]";
connectAttr "bindPose1.m[58]" "bindPose1.p[59]";
connectAttr "bindPose1.m[59]" "bindPose1.p[60]";
connectAttr "bindPose1.m[60]" "bindPose1.p[61]";
connectAttr "bindPose1.m[61]" "bindPose1.p[62]";
connectAttr "bindPose1.m[62]" "bindPose1.p[63]";
connectAttr "bindPose1.m[63]" "bindPose1.p[64]";
connectAttr "bindPose1.m[64]" "bindPose1.p[65]";
connectAttr "bindPose1.m[65]" "bindPose1.p[66]";
connectAttr "bindPose1.m[41]" "bindPose1.p[67]";
connectAttr "bindPose1.m[41]" "bindPose1.p[68]";
connectAttr "bindPose1.m[41]" "bindPose1.p[69]";
connectAttr "bindPose1.m[69]" "bindPose1.p[70]";
connectAttr "bindPose1.m[70]" "bindPose1.p[71]";
connectAttr "bindPose1.m[71]" "bindPose1.p[72]";
connectAttr "bindPose1.m[72]" "bindPose1.p[73]";
connectAttr "bindPose1.m[39]" "bindPose1.p[74]";
connectAttr "bindPose1.m[38]" "bindPose1.p[75]";
connectAttr "bindPose1.m[75]" "bindPose1.p[76]";
connectAttr "bindPose1.m[76]" "bindPose1.p[77]";
connectAttr "bindPose1.m[77]" "bindPose1.p[78]";
connectAttr "bindPose1.m[78]" "bindPose1.p[79]";
connectAttr "bindPose1.m[79]" "bindPose1.p[80]";
connectAttr "bindPose1.m[80]" "bindPose1.p[81]";
connectAttr "bindPose1.m[81]" "bindPose1.p[82]";
connectAttr "bindPose1.m[78]" "bindPose1.p[83]";
connectAttr "bindPose1.m[83]" "bindPose1.p[84]";
connectAttr "bindPose1.m[84]" "bindPose1.p[85]";
connectAttr "bindPose1.m[85]" "bindPose1.p[86]";
connectAttr "bindPose1.m[86]" "bindPose1.p[87]";
connectAttr "bindPose1.m[78]" "bindPose1.p[88]";
connectAttr "bindPose1.m[77]" "bindPose1.p[89]";
connectAttr "bindPose1.m[89]" "bindPose1.p[90]";
connectAttr "bindPose1.m[77]" "bindPose1.p[91]";
connectAttr "bindPose1.m[77]" "bindPose1.p[92]";
connectAttr "bindPose1.m[76]" "bindPose1.p[93]";
connectAttr "bindPose1.m[38]" "bindPose1.p[94]";
connectAttr "bindPose1.m[94]" "bindPose1.p[95]";
connectAttr "bindPose1.m[95]" "bindPose1.p[96]";
connectAttr "bindPose1.m[96]" "bindPose1.p[97]";
connectAttr "bindPose1.m[97]" "bindPose1.p[98]";
connectAttr "bindPose1.m[98]" "bindPose1.p[99]";
connectAttr "bindPose1.m[99]" "bindPose1.p[100]";
connectAttr "bindPose1.m[100]" "bindPose1.p[101]";
connectAttr "bindPose1.m[97]" "bindPose1.p[102]";
connectAttr "bindPose1.m[102]" "bindPose1.p[103]";
connectAttr "bindPose1.m[103]" "bindPose1.p[104]";
connectAttr "bindPose1.m[104]" "bindPose1.p[105]";
connectAttr "bindPose1.m[105]" "bindPose1.p[106]";
connectAttr "bindPose1.m[97]" "bindPose1.p[107]";
connectAttr "bindPose1.m[96]" "bindPose1.p[108]";
connectAttr "bindPose1.m[108]" "bindPose1.p[109]";
connectAttr "bindPose1.m[96]" "bindPose1.p[110]";
connectAttr "bindPose1.m[96]" "bindPose1.p[111]";
connectAttr "bindPose1.m[95]" "bindPose1.p[112]";
connectAttr "bindPose1.m[34]" "bindPose1.p[113]";
connectAttr "bindPose1.m[113]" "bindPose1.p[114]";
connectAttr "bindPose1.m[114]" "bindPose1.p[115]";
connectAttr "bindPose1.m[115]" "bindPose1.p[116]";
connectAttr "bindPose1.m[116]" "bindPose1.p[117]";
connectAttr "bindPose1.m[115]" "bindPose1.p[118]";
connectAttr "bindPose1.m[114]" "bindPose1.p[119]";
connectAttr "bindPose1.m[119]" "bindPose1.p[120]";
connectAttr "bindPose1.m[113]" "bindPose1.p[121]";
connectAttr "bindPose1.m[34]" "bindPose1.p[122]";
connectAttr "bindPose1.m[122]" "bindPose1.p[123]";
connectAttr "bindPose1.m[123]" "bindPose1.p[124]";
connectAttr "bindPose1.m[124]" "bindPose1.p[125]";
connectAttr "bindPose1.m[125]" "bindPose1.p[126]";
connectAttr "bindPose1.m[124]" "bindPose1.p[127]";
connectAttr "bindPose1.m[123]" "bindPose1.p[128]";
connectAttr "bindPose1.m[128]" "bindPose1.p[129]";
connectAttr "bindPose1.m[122]" "bindPose1.p[130]";
connectAttr "bindPose1.m[33]" "bindPose1.p[131]";
connectAttr "FBX_Hips.bps" "bindPose1.wm[34]";
connectAttr "FBX_Spine.bps" "bindPose1.wm[35]";
connectAttr "FBX_Spine1.bps" "bindPose1.wm[36]";
connectAttr "FBX_Spine2.bps" "bindPose1.wm[37]";
connectAttr "FBX_Spine3.bps" "bindPose1.wm[38]";
connectAttr "FBX_Neck.bps" "bindPose1.wm[39]";
connectAttr "FBX_Neck1.bps" "bindPose1.wm[40]";
connectAttr "FBX_Head.bps" "bindPose1.wm[41]";
connectAttr "FBX_LeftEye.bps" "bindPose1.wm[67]";
connectAttr "FBX_RightEye.bps" "bindPose1.wm[68]";
connectAttr "FBX_NeckRoll.bps" "bindPose1.wm[74]";
connectAttr "FBX_LeftShoulder.bps" "bindPose1.wm[75]";
connectAttr "FBX_LeftArm.bps" "bindPose1.wm[76]";
connectAttr "FBX_LeftForeArm.bps" "bindPose1.wm[77]";
connectAttr "FBX_LeftHand.bps" "bindPose1.wm[78]";
connectAttr "FBX_LeftHandThumb1.bps" "bindPose1.wm[79]";
connectAttr "FBX_LeftHandThumb2.bps" "bindPose1.wm[80]";
connectAttr "FBX_LeftHandThumb3.bps" "bindPose1.wm[81]";
connectAttr "FBX_LeftHandThumb4.bps" "bindPose1.wm[82]";
connectAttr "FBX_LeftHandMiddle0.bps" "bindPose1.wm[83]";
connectAttr "FBX_LeftHandMiddle1.bps" "bindPose1.wm[84]";
connectAttr "FBX_LeftHandMiddle2.bps" "bindPose1.wm[85]";
connectAttr "FBX_LeftHandMiddle3.bps" "bindPose1.wm[86]";
connectAttr "FBX_LeftHandMiddle4.bps" "bindPose1.wm[87]";
connectAttr "FBX_LeftHandRoll.bps" "bindPose1.wm[88]";
connectAttr "FBX_LeftElbowRoll.bps" "bindPose1.wm[89]";
connectAttr "FBX_LeftElbowRoll_End.bps" "bindPose1.wm[90]";
connectAttr "FBX_LeftForeArmRoll.bps" "bindPose1.wm[91]";
connectAttr "FBX_LeftForeArmRoll1.bps" "bindPose1.wm[92]";
connectAttr "FBX_LeftArmRoll.bps" "bindPose1.wm[93]";
connectAttr "FBX_RightShoulder.bps" "bindPose1.wm[94]";
connectAttr "FBX_RightArm.bps" "bindPose1.wm[95]";
connectAttr "FBX_RightForeArm.bps" "bindPose1.wm[96]";
connectAttr "FBX_RightHand.bps" "bindPose1.wm[97]";
connectAttr "FBX_RightHandThumb1.bps" "bindPose1.wm[98]";
connectAttr "FBX_RightHandThumb2.bps" "bindPose1.wm[99]";
connectAttr "FBX_RightHandThumb3.bps" "bindPose1.wm[100]";
connectAttr "FBX_RightHandThumb4.bps" "bindPose1.wm[101]";
connectAttr "FBX_RightHandMiddle0.bps" "bindPose1.wm[102]";
connectAttr "FBX_RightHandMiddle1.bps" "bindPose1.wm[103]";
connectAttr "FBX_RightHandMiddle2.bps" "bindPose1.wm[104]";
connectAttr "FBX_RightHandMiddle3.bps" "bindPose1.wm[105]";
connectAttr "FBX_RightHandMiddle4.bps" "bindPose1.wm[106]";
connectAttr "FBX_RightHandRoll.bps" "bindPose1.wm[107]";
connectAttr "FBX_RightElbowRoll.bps" "bindPose1.wm[108]";
connectAttr "FBX_RightElbowRoll_End.bps" "bindPose1.wm[109]";
connectAttr "FBX_RightForeArmRoll.bps" "bindPose1.wm[110]";
connectAttr "FBX_RightForeArmRoll1.bps" "bindPose1.wm[111]";
connectAttr "FBX_RightArmRoll.bps" "bindPose1.wm[112]";
connectAttr "FBX_LeftUpLeg.bps" "bindPose1.wm[113]";
connectAttr "FBX_LeftLeg.bps" "bindPose1.wm[114]";
connectAttr "FBX_LeftFoot.bps" "bindPose1.wm[115]";
connectAttr "FBX_LeftToeBase.bps" "bindPose1.wm[116]";
connectAttr "FBX_LeftToes_End.bps" "bindPose1.wm[117]";
connectAttr "FBX_LeftFootRoll.bps" "bindPose1.wm[118]";
connectAttr "FBX_LeftKneeRoll.bps" "bindPose1.wm[119]";
connectAttr "FBX_LeftKneeRoll_End.bps" "bindPose1.wm[120]";
connectAttr "FBX_LeftUpLegRoll.bps" "bindPose1.wm[121]";
connectAttr "FBX_RightUpLeg.bps" "bindPose1.wm[122]";
connectAttr "FBX_RightLeg.bps" "bindPose1.wm[123]";
connectAttr "FBX_RightFoot.bps" "bindPose1.wm[124]";
connectAttr "FBX_RightToeBase.bps" "bindPose1.wm[125]";
connectAttr "FBX_RightToes_End.bps" "bindPose1.wm[126]";
connectAttr "FBX_RightFootRoll.bps" "bindPose1.wm[127]";
connectAttr "FBX_RightKneeRoll.bps" "bindPose1.wm[128]";
connectAttr "FBX_RightKneeRoll_End.bps" "bindPose1.wm[129]";
connectAttr "FBX_RightUpLegRoll.bps" "bindPose1.wm[130]";
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
connectAttr "|FBX_Hips|pCube1|pCubeShape1.iog" ":initialShadingGroup.dsm" -na;
connectAttr "|FBX_Hips|FBX_RightUpLeg|pCube2|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_LeftUpLeg|pCube3|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_RightUpLeg|FBX_RightLeg|pCube4|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_LeftUpLeg|FBX_LeftLeg|pCube5|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_RightUpLeg|FBX_RightLeg|FBX_RightFoot|pCube6|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_LeftUpLeg|FBX_LeftLeg|FBX_LeftFoot|pCube7|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|pCube8|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|pCube9|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_LeftShoulder|pCube10|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_RightShoulder|pCube11|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_RightShoulder|FBX_RightArm|pCube12|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_LeftShoulder|FBX_LeftArm|FBX_LeftForeArm|pCube13|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_LeftShoulder|FBX_LeftArm|pCube14|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_RightShoulder|FBX_RightArm|FBX_RightForeArm|pCube15|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|FBX_Hips|FBX_Spine|FBX_Spine1|FBX_Spine2|FBX_Spine3|FBX_Neck|FBX_Neck1|pCube16|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
// End of skel2.ma
