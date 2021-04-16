"""Temporary test file"""

from dataclasses import dataclass
from lark import Token
from lark.tree import Tree
from main import Document
from typing import List
from itertools import chain

FILE = '''
J0: EEEA + B -> 6Ceek; Something * 2
'''

FILE = '''
J0: SA -> SB +??; E10
A == 2
J0: S48 + S17 -> S46; E0*(k0*S48*S17 - k0r*S46);
J1: S67 -> S50 + S8; E1*(k1*S67 - k1r*S50*S8);
J2: S2 + S47 -> S40; E2*(k2*S2*S47 - k2r*S40);
J3: S88 -> S99; E3*(k3*S88 - k3r*S99);
J4: S98 -> S65; E4*(k4*S98 - k4r*S65);
J5: S2 + S11 -> S50; E5*(k5*S2*S11 - k5r*S50);
J6: S49 -> S90 + S5; E6*(k6*S49 - k6r*S90*S5);
J7: S45 -> S30 + S66; E7*(k7*S45 - k7r*S30*S66);
J8: S73 + S83 -> S71; E8*(k8*S73*S83 - k8r*S71);
J9: S45 -> S28 + S12; E9*(k9*S45 - k9r*S28*S12);
J10: S4 + S1 -> S84; E10*(k10*S4*S1 - k10r*S84);
J11: S97 -> S99 + S2; E11*(k11*S97 - k11r*S99*S2);
J12: S97 -> S74; E12*(k12*S97 - k12r*S74);
J13: S76 -> S65; E13*(k13*S76 - k13r*S65);
J14: S51 -> S49 + S32; E14*(k14*S51 - k14r*S49*S32);
J15: S50 -> S38; E15*(k15*S50 - k15r*S38);
J16: S0 + S14 -> S28; E16*(k16*S0*S14 - k16r*S28);
J17: S82 + S23 -> S0; E17*(k17*S82*S23 - k17r*S0);
J18: S10 -> S38 + S87; E18*(k18*S10 - k18r*S38*S87);
J19: S54 -> S16; E19*(k19*S54 - k19r*S16);
J20: S37 + S10 -> S92; E20*(k20*S37*S10 - k20r*S92);
J21: S8 + S16 -> S59; E21*(k21*S8*S16 - k21r*S59);
J22: S87 -> S17 + S22; E22*(k22*S87 - k22r*S17*S22);
J23: S9 -> S22; E23*(k23*S9 - k23r*S22);
J24: S21 -> S56 + S82; E24*(k24*S21 - k24r*S56*S82);
J25: S11 -> S59 + S40; E25*(k25*S11 - k25r*S59*S40);
J26: S1 -> S70; E26*(k26*S1 - k26r*S70);
J27: S24 -> S74; E27*(k27*S24 - k27r*S74);
J28: S86 -> S79; E28*(k28*S86 - k28r*S79);
J29: S42 -> S24; E29*(k29*S42 - k29r*S24);
J30: S82 -> S9; E30*(k30*S82 - k30r*S9);
J31: S47 -> S65; E31*(k31*S47 - k31r*S65);
J32: S91 + S4 -> S3; E32*(k32*S91*S4 - k32r*S3);
J33: S41 -> S73 + S15; E33*(k33*S41 - k33r*S73*S15);
J34: S92 -> S14 + S78; E34*(k34*S92 - k34r*S14*S78);
J35: S49 -> S19; E35*(k35*S49 - k35r*S19);
J36: S70 -> S91 + S99; E36*(k36*S70 - k36r*S91*S99);
J37: S85 -> S48 + S42; E37*(k37*S85 - k37r*S48*S42);
J38: S5 -> S50 + S30; E38*(k38*S5 - k38r*S50*S30);
J39: S5 -> S40 + S81; E39*(k39*S5 - k39r*S40*S81);
J40: S53 -> S54 + S4; E40*(k40*S53 - k40r*S54*S4);
J41: S66 + S41 -> S70; E41*(k41*S66*S41 - k41r*S70);
J42: S46 -> S28 + S72; E42*(k42*S46 - k42r*S28*S72);
J43: S2 + S24 -> S17; E43*(k43*S2*S24 - k43r*S17);
J44: S89 -> S33; E44*(k44*S89 - k44r*S33);
J45: S81 -> S35; E45*(k45*S81 - k45r*S35);
J46: S73 -> S19 + S95; E46*(k46*S73 - k46r*S19*S95);
J47: S93 -> S97; E47*(k47*S93 - k47r*S97);
J48: S48 -> S27 + S23; E48*(k48*S48 - k48r*S27*S23);
J49: S80 -> S26; E49*(k49*S80 - k49r*S26);
J50: S81 -> S8; E50*(k50*S81 - k50r*S8);
J51: S35 -> S0 + S13; E51*(k51*S35 - k51r*S0*S13);
J52: S79 -> S50 + S99; E52*(k52*S79 - k52r*S50*S99);
J53: S8 -> S64; E53*(k53*S8 - k53r*S64);
J54: S89 -> S20 + S52; E54*(k54*S89 - k54r*S20*S52);
J55: S70 -> S15 + S87; E55*(k55*S70 - k55r*S15*S87);
J56: S12 + S16 -> S6; E56*(k56*S12*S16 - k56r*S6);
J57: S4 -> S27 + S24; E57*(k57*S4 - k57r*S27*S24);
J58: S0 + S51 -> S95; E58*(k58*S0*S51 - k58r*S95);
J59: S55 + S52 -> S17; E59*(k59*S55*S52 - k59r*S17);
J60: S76 -> S75; E60*(k60*S76 - k60r*S75);
J61: S38 -> S81; E61*(k61*S38 - k61r*S81);
J62: S84 -> S36 + S34; E62*(k62*S84 - k62r*S36*S34);
J63: S44 + S60 -> S35; E63*(k63*S44*S60 - k63r*S35);
J64: S6 -> S4; E64*(k64*S6 - k64r*S4);
J65: S31 + S79 -> S8; E65*(k65*S31*S79 - k65r*S8);
J66: S91 -> S71 + S10; E66*(k66*S91 - k66r*S71*S10);
J67: S76 + S12 -> S85; E67*(k67*S76*S12 - k67r*S85);
J68: S77 -> S3 + S81; E68*(k68*S77 - k68r*S3*S81);
J69: S30 -> S71; E69*(k69*S30 - k69r*S71);
J70: S71 -> S74; E70*(k70*S71 - k70r*S74);
J71: S21 -> S67 + S98; E71*(k71*S21 - k71r*S67*S98);
J72: S95 -> S27; E72*(k72*S95 - k72r*S27);
J73: S82 + S68 -> S10; E73*(k73*S82*S68 - k73r*S10);
J74: S71 -> S24; E74*(k74*S71 - k74r*S24);
J75: S32 -> S71; E75*(k75*S32 - k75r*S71);
J76: S3 + S46 -> S74; E76*(k76*S3*S46 - k76r*S74);
J77: S56 + S5 -> S11; E77*(k77*S56*S5 - k77r*S11);
J78: S82 + S83 -> S75; E78*(k78*S82*S83 - k78r*S75);
J79: S62 -> S86; E79*(k79*S62 - k79r*S86);
J80: S8 -> S91 + S41; E80*(k80*S8 - k80r*S91*S41);
J81: S6 -> S46; E81*(k81*S6 - k81r*S46);
J82: S9 + S12 -> S22; E82*(k82*S9*S12 - k82r*S22);
J83: S55 -> S86 + S77; E83*(k83*S55 - k83r*S86*S77);
J84: S31 + S71 -> S66; E84*(k84*S31*S71 - k84r*S66);
J85: S80 + S58 -> S78; E85*(k85*S80*S58 - k85r*S78);
J86: S64 + S89 -> S35; E86*(k86*S64*S89 - k86r*S35);
J87: S11 -> S68; E87*(k87*S11 - k87r*S68);
J88: S31 -> S37; E88*(k88*S31 - k88r*S37);
J89: S47 -> S50; E89*(k89*S47 - k89r*S50);
J90: S79 -> S29; E90*(k90*S79 - k90r*S29);
J91: S5 -> S57; E91*(k91*S5 - k91r*S57);
J92: S22 -> S84; E92*(k92*S22 - k92r*S84);
J93: S99 -> S97 + S2; E93*(k93*S99 - k93r*S97*S2);
J94: S64 -> S67 + S35; E94*(k94*S64 - k94r*S67*S35);
J95: S8 -> S7 + S30; E95*(k95*S8 - k95r*S7*S30);
J96: S8 -> S22; E96*(k96*S8 - k96r*S22);
J97: S79 + S36 -> S24; E97*(k97*S79*S36 - k97r*S24);
J98: S40 + S89 -> S76; E98*(k98*S40*S89 - k98r*S76);
J99: S85 -> S12; E99*(k99*S85 - k99r*S12);
J100: S28 -> S0; E100*(k100*S28 - k100r*S0);
J101: S34 + S80 -> S45; E101*(k101*S34*S80 - k101r*S45);
J102: S48 + S83 -> S25; E102*(k102*S48*S83 - k102r*S25);
J103: S55 -> S59; E103*(k103*S55 - k103r*S59);
J104: S67 -> S94 + S27; E104*(k104*S67 - k104r*S94*S27);
J105: S58 -> S93; E105*(k105*S58 - k105r*S93);
J106: S40 + S69 -> S37; E106*(k106*S40*S69 - k106r*S37);
J107: S80 -> S19; E107*(k107*S80 - k107r*S19);
J108: S4 -> S26; E108*(k108*S4 - k108r*S26);
J109: S30 + S50 -> S94; E109*(k109*S30*S50 - k109r*S94);
J110: S13 -> S69; E110*(k110*S13 - k110r*S69);
J111: S89 -> S72 + S27; E111*(k111*S89 - k111r*S72*S27);
J112: S68 -> S15; E112*(k112*S68 - k112r*S15);
J113: S98 -> S65 + S93; E113*(k113*S98 - k113r*S65*S93);
J114: S28 -> S74 + S13; E114*(k114*S28 - k114r*S74*S13);
J115: S30 + S29 -> S70; E115*(k115*S30*S29 - k115r*S70);
J116: S95 -> S1; E116*(k116*S95 - k116r*S1);
J117: S28 -> S97 + S72; E117*(k117*S28 - k117r*S97*S72);
J118: S40 -> S56; E118*(k118*S40 - k118r*S56);
J119: S29 + S83 -> S80; E119*(k119*S29*S83 - k119r*S80);
J120: S78 + S78 -> S65; E120*(k120*S78*S78 - k120r*S65);
J121: S66 -> S1; E121*(k121*S66 - k121r*S1);
J122: S90 + S42 -> S11; E122*(k122*S90*S42 - k122r*S11);
J123: S97 -> S35 + S75; E123*(k123*S97 - k123r*S35*S75);
J124: S21 -> S82 + S5; E124*(k124*S21 - k124r*S82*S5);
J125: S88 -> S72; E125*(k125*S88 - k125r*S72);
J126: S4 -> S0; E126*(k126*S4 - k126r*S0);
J127: S40 -> S44; E127*(k127*S40 - k127r*S44);
J128: S70 -> S6; E128*(k128*S70 - k128r*S6);
J129: S49 -> S6 + S62; E129*(k129*S49 - k129r*S6*S62);
J130: S96 -> S49; E130*(k130*S96 - k130r*S49);
J131: S46 + S79 -> S38; E131*(k131*S46*S79 - k131r*S38);
J132: S24 -> S7; E132*(k132*S24 - k132r*S7);
J133: S87 -> S38; E133*(k133*S87 - k133r*S38);
J134: S89 -> S90; E134*(k134*S89 - k134r*S90);
J135: S95 + S93 -> S21; E135*(k135*S95*S93 - k135r*S21);
J136: S51 + S19 -> S22; E136*(k136*S51*S19 - k136r*S22);
J137: S92 -> S49 + S26; E137*(k137*S92 - k137r*S49*S26);
J138: S98 -> S38 + S19; E138*(k138*S98 - k138r*S38*S19);
J139: S36 -> S31 + S45; E139*(k139*S36 - k139r*S31*S45);
J140: S40 + S21 -> S72; E140*(k140*S40*S21 - k140r*S72);
J141: S97 -> S84 + S93; E141*(k141*S97 - k141r*S84*S93);
J142: S27 -> S57; E142*(k142*S27 - k142r*S57);
J143: S70 -> S68; E143*(k143*S70 - k143r*S68);
J144: S68 -> S98 + S40; E144*(k144*S68 - k144r*S98*S40);
J145: S5 -> S63; E145*(k145*S5 - k145r*S63);
J146: S70 + S51 -> S14; E146*(k146*S70*S51 - k146r*S14);
J147: S40 -> S81 + S58; E147*(k147*S40 - k147r*S81*S58);
J148: S89 -> S60; E148*(k148*S89 - k148r*S60);
J149: S31 + S80 -> S37; E149*(k149*S31*S80 - k149r*S37);

k0 = 0.5217754063290215
k0r = 0.5245809488094159
k1 = 0.951070107165509
k1r = 0.07205304466715279
k2 = 0.042568281628443505
k2r = 0.07698127443235747
k3 = 0.4423766692363408
k3r = 0.8524034584155115
k4 = 0.7451975674859153
k4r = 0.813006204086284
k5 = 0.9588536434925068
k5r = 0.33530445779439433
k6 = 0.7841500850107231
k6r = 0.7933020081132071
k7 = 0.6664714430939817
k7r = 0.6828199890007731
k8 = 0.6067455309963199
k8r = 0.9793383259730012
k9 = 0.43443736224048135
k9r = 0.14027934054202273
k10 = 0.5482848235816639
k10r = 0.9472122429012658
k11 = 0.33663243648276975
k11r = 0.15295851639087277
k12 = 0.7509312126563144
k12r = 0.39290997042282316
k13 = 0.7721634295559655
k13r = 0.18164273931833785
k14 = 0.17344639063964284
k14r = 0.847337603969264
k15 = 0.5669681908967931
k15r = 0.8543142134689257
k16 = 0.6621513715431632
k16r = 0.5707440412414495
k17 = 0.7693310873103498
k17r = 0.5990868529599949
k18 = 0.3837417695089723
k18r = 0.19123875780162203
k19 = 0.123619116629753
k19r = 0.8240209958560906
k20 = 0.8856183901122705
k20r = 0.3016167000749236
k21 = 0.09867829270882522
k21r = 0.9397371478050282
k22 = 0.67529668742231
k22r = 0.09555097381538369
k23 = 0.22310191793681033
k23r = 0.7453460204955935
k24 = 0.7400702435877724
k24r = 0.9292288020645697
k25 = 0.6026603025198676
k25r = 0.5724071231194412
k26 = 0.9809180939914598
k26r = 0.2882502918091199
k27 = 0.6275050621658745
k27r = 0.2545642273902671
k28 = 0.24068619678099024
k28r = 0.34032537967581367
k29 = 0.767576419006543
k29r = 0.3873126919790981
k30 = 0.28406402898624683
k30r = 0.344290211872912
k31 = 0.36662015085177957
k31r = 0.2494905320804598
k32 = 0.6261680707534806
k32r = 0.9895849916852174
k33 = 0.15075268148092047
k33r = 0.3399495269621877
k34 = 0.5297914689414676
k34r = 0.03689776764644592
k35 = 0.4573209634467199
k35r = 0.1209932186631778
k36 = 0.960113239780942
k36r = 0.18347087054883005
k37 = 0.3201229436955757
k37r = 0.24554504010870626
k38 = 0.712155189789234
k38r = 0.9737238048944267
k39 = 0.10196795515709522
k39r = 0.4615763936307459
k40 = 0.23471004090616698
k40r = 0.7801171180154578
k41 = 0.637252337503815
k41r = 0.6792493522798267
k42 = 0.9903023602568832
k42r = 0.03104021388919287
k43 = 0.12763970354706977
k43r = 0.3028566417784606
k44 = 0.06584769376682831
k44r = 0.6057349017148104
k45 = 0.8396636709556139
k45r = 0.9464407888783413
k46 = 0.6276892993485577
k46r = 0.8771177588624267
k47 = 0.3855552698173984
k47r = 0.5772998757830327
k48 = 0.8385011286320664
k48r = 0.06761873140855479
k49 = 0.5393673691804162
k49r = 0.8151941544546496
k50 = 0.3811740675783387
k50r = 0.8439105465127796
k51 = 0.020197376798368638
k51r = 0.5551235632386577
k52 = 0.8170581740427821
k52r = 0.7450758794261833
k53 = 0.2853226507451274
k53r = 0.12496577180204271
k54 = 0.7905280820081905
k54r = 0.9874838794367818
k55 = 0.12922152283559274
k55r = 0.5673031102049341
k56 = 0.24635482492014193
k56r = 0.9124949933587385
k57 = 0.1786068741232283
k57r = 0.30863869805453503
k58 = 0.7310302076247792
k58r = 0.2785809572576441
k59 = 0.7115802867325743
k59r = 0.6457709384288147
k60 = 0.7826580781101807
k60r = 0.1933669775873159
k61 = 0.8581089819422365
k61r = 0.8582530798661854
k62 = 0.8900408685102189
k62r = 0.43174661834995653
k63 = 0.2722758682495272
k63r = 0.5596027534905498
k64 = 0.029657435426545642
k64r = 0.2957455719807611
k65 = 0.5975494007816692
k65r = 0.5892804817856019
k66 = 0.23528440001563
k66r = 0.5295820783712085
k67 = 0.7435476866623004
k67r = 0.7796030763086139
k68 = 0.7899150634016175
k68r = 0.9462519645900768
k69 = 0.3996906301439054
k69r = 0.8789054362365618
k70 = 0.6977081376491504
k70r = 0.5940448815589966
k71 = 0.5635150199610527
k71r = 0.40951161914306256
k72 = 0.4522934184200933
k72r = 0.9096230458059615
k73 = 0.6389766540212655
k73r = 0.49655861393119893
k74 = 0.975126189356944
k74r = 0.7474917774569684
k75 = 0.3012784299819109
k75r = 0.7202646777973519
k76 = 0.5861206687338697
k76r = 0.2995941337763991
k77 = 0.9319395053796666
k77r = 0.7396364899386165
k78 = 0.3958609019016476
k78r = 0.7152191656687779
k79 = 0.3888092118493386
k79r = 0.13417112047342195
k80 = 0.4424811229491903
k80r = 0.8548220380101564
k81 = 0.39496113498106533
k81r = 0.08790874886081934
k82 = 0.20870827836917916
k82r = 0.6435738424133459
k83 = 0.48983625166731004
k83r = 0.7747882341638979
k84 = 0.03095526162776474
k84r = 0.8599558719284016
k85 = 0.8952073559486057
k85r = 0.9769823305198854
k86 = 0.7333745305474181
k86r = 0.27854724981045675
k87 = 0.44811634865113803
k87r = 0.8851199915701142
k88 = 0.9251855587737927
k88r = 0.8840074307332811
k89 = 0.16623089054571694
k89r = 0.5800348217558349
k90 = 0.2318291819125392
k90r = 0.21704087236204772
k91 = 0.9161400482422708
k91r = 0.01044407735012487
k92 = 0.6541088093935626
k92r = 0.1167634129854771
k93 = 0.22373122579509508
k93r = 0.5873450945055462
k94 = 0.019054463520688958
k94r = 0.9360523528143135
k95 = 0.4200135506664543
k95r = 0.906420692791488
k96 = 0.005250570127762533
k96r = 0.37159105352000965
k97 = 0.4851863620349708
k97r = 0.3877605878284479
k98 = 0.43460550423712685
k98r = 0.6434307679248273
k99 = 0.6418755130242769
k99r = 0.6735250250718658
k100 = 0.7097195474407147
k100r = 0.2970562338788798
k101 = 0.934305903587565
k101r = 0.7162622100619487
k102 = 0.1578970311490805
k102r = 0.3996545730731431
k103 = 0.13885342547602963
k103r = 0.6505759444572387
k104 = 0.4825006514075345
k104r = 0.2796188012313897
k105 = 0.7837556324902692
k105r = 0.7922060051017553
k106 = 0.7365754570646424
k106r = 0.8298017721496439
k107 = 0.0374779114715873
k107r = 0.3274474062288708
k108 = 0.24168012581556508
k108r = 0.0303786319444741
k109 = 0.45687853050018945
k109r = 0.17872259803879043
k110 = 0.269538867969234
k110r = 0.6982165384359276
k111 = 0.6435915600992268
k111r = 0.6478407567312409
k112 = 0.49463545352688865
k112r = 0.08625494814597434
k113 = 0.007068886019159226
k113r = 0.21469583171760154
k114 = 0.2789534784123302
k114r = 0.870485713113102
k115 = 0.7164505209700923
k115r = 0.10589021029009016
k116 = 0.453145977260456
k116r = 0.7973087304926557
k117 = 0.13730957320351433
k117r = 0.5687437307994245
k118 = 0.7925086290088416
k118r = 0.9869765722094882
k119 = 0.3201879520941582
k119r = 0.45151012653795064
k120 = 0.2875399412070089
k120r = 0.5187857122820385
k121 = 0.8101500395549958
k121r = 0.007238113606004015
k122 = 0.9303047151277781
k122r = 0.949120216064204
k123 = 0.6803049375676661
k123r = 0.2232729842892308
k124 = 0.7375684140975227
k124r = 0.2981226934382607
k125 = 0.347848048277116
k125r = 0.9583855068145565
k126 = 0.25935435291382614
k126r = 0.5247799449566755
k127 = 0.94357457015425
k127r = 0.9880519841097458
k128 = 0.39787246016500244
k128r = 0.24316845583555946
k129 = 0.2416934512473371
k129r = 0.012389478221273231
k130 = 0.033912551390242296
k130r = 0.3227002024647255
k131 = 0.4591246248859865
k131r = 0.03929843383179665
k132 = 0.7001229450904707
k132r = 0.4873847582269486
k133 = 0.11214442400432478
k133r = 0.4913725217084105
k134 = 0.8154828335732094
k134r = 0.6817474518628236
k135 = 0.3858340979761474
k135r = 0.7706491926651577
k136 = 0.26808081517589877
k136r = 0.36749315647670433
k137 = 0.35061972036533207
k137r = 0.3348394793182361
k138 = 0.8950563014261573
k138r = 0.3631739980542795
k139 = 0.6284854302399083
k139r = 0.8832556134477392
k140 = 0.603193745372783
k140r = 0.2363109101669839
k141 = 0.6354098700932922
k141r = 0.659319109431048
k142 = 0.356539188569474
k142r = 0.8360618859891333
k143 = 0.5035408276144239
k143r = 0.9373790049015741
k144 = 0.3530436268804964
k144r = 0.03381268534513382
k145 = 0.242175389578821
k145r = 0.31336210374892504
k146 = 0.7453697965038772
k146r = 0.8268283038625811
k147 = 0.7760603555669381
k147r = 0.8252292373727106
k148 = 0.9996013235492862
k148r = 0.8271232781928043
k149 = 0.3140769713812155
k149r = 0.8618065318864245

E0 = 1
E1 = 1
E2 = 1
E3 = 1
E4 = 1
E5 = 1
E6 = 1
E7 = 1
E8 = 1
E9 = 1
E10 = 1
E11 = 1
E12 = 1
E13 = 1
E14 = 1
E15 = 1
E16 = 1
E17 = 1
E18 = 1
E19 = 1
E20 = 1
E21 = 1
E22 = 1
E23 = 1
E24 = 1
E25 = 1
E26 = 1
E27 = 1
E28 = 1
E29 = 1
E30 = 1
E31 = 1
E32 = 1
E33 = 1
E34 = 1
E35 = 1
E36 = 1
E37 = 1
E38 = 1
E39 = 1
E40 = 1
E41 = 1
E42 = 1
E43 = 1
E44 = 1
E45 = 1
E46 = 1
E47 = 1
E48 = 1
E49 = 1
E50 = 1
E51 = 1
E52 = 1
E53 = 1
E54 = 1
E55 = 1
E56 = 1
E57 = 1
E58 = 1
E59 = 1
E60 = 1
E61 = 1
E62 = 1
E63 = 1
E64 = 1
E65 = 1
E66 = 1
E67 = 1
E68 = 1
E69 = 1
E70 = 1
E71 = 1
E72 = 1
E73 = 1
E74 = 1
E75 = 1
E76 = 1
E77 = 1
E78 = 1
E79 = 1
E80 = 1
E81 = 1
E82 = 1
E83 = 1
E84 = 1
E85 = 1
E86 = 1
E87 = 1
E88 = 1
E89 = 1
E90 = 1
E91 = 1
E92 = 1
E93 = 1
E94 = 1
E95 = 1
E96 = 1
E97 = 1
E98 = 1
E99 = 1
E100 = 1
E101 = 1
E102 = 1
E103 = 1
E104 = 1
E105 = 1
E106 = 1
E107 = 1
E108 = 1
E109 = 1
E110 = 1
E111 = 1
E112 = 1
E113 = 1
E114 = 1
E115 = 1
E116 = 1
E117 = 1
E118 = 1
E119 = 1
E120 = 1
E121 = 1
E122 = 1
E123 = 1
E124 = 1
E125 = 1
E126 = 1
E127 = 1
E128 = 1
E129 = 1
E130 = 1
E131 = 1
E132 = 1
E133 = 1
E134 = 1
E135 = 1
E136 = 1
E137 = 1
E138 = 1
E139 = 1
E140 = 1
E141 = 1
E142 = 1
E143 = 1
E144 = 1
E145 = 1
E146 = 1
E147 = 1
E148 = 1
E149 = 1

S7 = 5
S15 = 3
S20 = 6
S25 = 1
S26 = 5
S33 = 5
S47 = 4
S51 = 4
S53 = 2
S55 = 4
S57 = 1
S59 = 6
S63 = 6
S65 = 4
S72 = 4
S74 = 2
S75 = 4
S83 = 4
S88 = 5
S89 = 1
S94 = 5
S96 = 4

S0 = 5
S1 = 6
S2 = 6
S3 = 2
S4 = 1
S5 = 3
S6 = 3
S8 = 4
S9 = 1
S10 = 6
S11 = 2
S12 = 4
S13 = 5
S14 = 2
S16 = 5
S17 = 6
S19 = 5
S21 = 5
S22 = 2
S23 = 2
S24 = 1
S27 = 2
S28 = 5
S29 = 3
S30 = 3
S31 = 1
S32 = 2
S34 = 6
S35 = 4
S36 = 3
S37 = 5
S38 = 5
S40 = 1
S41 = 6
S42 = 3
S44 = 2
S45 = 2
S46 = 6
S48 = 1
S49 = 1
S50 = 2
S52 = 2
S54 = 3
S56 = 5
S58 = 3
S60 = 3
S62 = 1
S64 = 4
S66 = 6
S67 = 2
S68 = 5
S69 = 5
S70 = 4
S71 = 5
S73 = 3
S76 = 5
S77 = 2
S78 = 5
S79 = 5
S80 = 2
S81 = 6
S82 = 4
S84 = 4
S85 = 6
S86 = 4
S87 = 6
S90 = 2
S91 = 5
S92 = 4
S93 = 3
S95 = 6
S97 = 1
S98 = 3
S99 = 3

'''


@dataclass
class Species:
    stoich: str
    name: str


@dataclass
class Reaction:
    reactants: List[Species]
    products: List[Species]
    rate_law: str

@dataclass
class Assignment:
    name: str
    value: str


def join_tokens(tokens):
    return ''.join(str(tok) for tok in tokens)


def walk_species_list(tree):
    ret = list()
    for species in tree.children:
        assert species.data == 'species'
        # assert not isinstance(species, str)
        stoich = None
        name = None
        if len(species.children) == 1:
            stoich = '1'
            name = join_tokens(species.children[0].children)
        else:
            assert len(species.children) == 2
            stoich = str(species.children[0])
            name = join_tokens(species.children[1].children)

        assert name is not None
        ret.append(Species(stoich, name))

    return ret


doc = Document(FILE)
