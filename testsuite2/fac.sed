#n
# $n = 30;
# > GET 30
s/.*/30/
# < GET
# > SET $n
x
s/;$n;[0-9]\+//
G
s/\n/;$n;/
x
# < SET
# $i  = 1;
# > GET 1
s/.*/1/
# < GET
# > SET $i
x
s/;$i;[0-9]\+//
G
s/\n/;$i;/
x
# < SET
# $r  = 1;
# > GET 1
s/.*/1/
# < GET
# > SET $r
x
s/;$r;[0-9]\+//
G
s/\n/;$r;/
x
# < SET
# while  ($i <= $n)
:LP10000
# > GET $i
g
/;$i;/!{
s/.*/$i/
b erudv
}
s/^.*;$i;\([0-9]*\).*/\1/
# < GET
# > PUSH
G
s/\n/;/
h
s/;.*//
# < PUSH
# > GET $n
g
/;$n;/!{
s/.*/$n/
b erudv
}
s/^.*;$n;\([0-9]*\).*/\1/
# < GET
# > SWAP
G
s/^\(.*\)\n\([^;]*;\)/\2\1;/
h
s/^[^;]*;//
x
s/;.*//
# < SWAP
# > LE
# > CAT 
G
s/^\([0-9]*\)\n\([0-9]*\);.*/\1;\2;/
# < CAT
# > CMP
s/;/!;/g
: LP20000
s/\([0-9]\)!\([0-9]*\);\([0-9]*\)\([0-9]\)!/!\1\2;\3!\4/
t LP20000
/^!/!b LP20003
/;!/!b LP20002
s/^!\([0-9]*\)\([0-9]*\);!\1\([0-9]*\);/\2;\3;/
/^;;$/ s//1/
/^1$/b LP20001
s/$/9876543210/
/^\(.\)[0-9]*;\(.\)[0-9]*;.*\1.*\2/b LP20003
:LP20002
s/.*/0/
b LP20001
:LP20003
s/.*/2/
:LP20001
# < CMP
y/012/110/
# < LE
# > DROP
x
s/^[^;]*;//
x
# < DROP
# > JZ LP10001
/^0$/b LP10001
# < JZ
# $r  = $r * $i;
# > GET $r
g
/;$r;/!{
s/.*/$r/
b erudv
}
s/^.*;$r;\([0-9]*\).*/\1/
# < GET
# > PUSH
G
s/\n/;/
h
s/;.*//
# < PUSH
# > GET $i
g
/;$i;/!{
s/.*/$i/
b erudv
}
s/^.*;$i;\([0-9]*\).*/\1/
# < GET
# > SWAP
G
s/^\(.*\)\n\([^;]*;\)/\2\1;/
h
s/^[^;]*;//
x
s/;.*//
# < SWAP
# > MUL
# > CAT 
G
s/^\([0-9]*\)\n\([0-9]*\);.*/\1;\2;/
# < CAT
G
h
s/\([0-9]*;[0-9]*;\).*/\1/
# > CMP
s/;/!;/g
: LP20005
s/\([0-9]\)!\([0-9]*\);\([0-9]*\)\([0-9]\)!/!\1\2;\3!\4/
t LP20005
/^!/!b LP20008
/;!/!b LP20007
s/^!\([0-9]*\)\([0-9]*\);!\1\([0-9]*\);/\2;\3;/
/^;;$/ s//1/
/^1$/b LP20006
s/$/9876543210/
/^\(.\)[0-9]*;\(.\)[0-9]*;.*\1.*\2/b LP20008
:LP20007
s/.*/0/
b LP20006
:LP20008
s/.*/2/
:LP20006
# < CMP
G
h
s/.*\n.*\n//
x
/^0\n/ s/^.\n\([0-9]*\);\([0-9]*\);\n.*/\2;\1;/
/^1\n/ s/^.\n\([0-9]*\);\([0-9]*\);\n.*/\1;\2;/
/^2\n/ s/^.\n\([0-9]*\);\([0-9]*\);\n.*/\1;\2;/
G
s/\n//
s/^/0;;/
:LP20004
s/^\([0-9]*;\)\([0-9]*;\)\([0-9]*;\)\([0-9]*\)\([0-9]\);/\3\5;\1\2\3\4;/
h
s/^[0-9]*;[0-9];//
x
s/^\([0-9]*;[0-9]\).*/\1/
/;0$/{
s/.*/0/
b LP20010
}
/;1$/{
s///
b LP20010
}
s/^/0;/
:LP20009
s/^\([0-9]*\);\([0-9]*\)\([0-9]\);\([0-9]\)/\3\4\1;\2;\4/
s/^\(..\)/\19876543210!/
s/^\(.\)\(.\)[0-9]*\1[0-9]*\2[0-9]*!/\2\1/
s/^\(..\)9876543210!/\1/
s/^\(..\)/\1!0000!0100!0200!0300!0400!0500!0600!0700!0800!0900!1101!1202!1303!1404!1505!1606!1707!1808!1909!2204!2306!2408!2510!2612!2714!2816!2918!3309!3412!3515!3618!3721!3824!3927!4416!4520!4624!4728!4832!4936!5525!5630!5735!5840!5945!6636!6742!6848!6954!7749!7856!7963!8864!8972!9981\
/
s/^\(..\).*!\1\(..\).*\n/\2/
s/^\(...\)/\19876543210!/
s/^\(.\)\(.\)\(.\)[0-9]*\2[0-9]*\3[0-9]*!/\1\3\2/
s/^\(...\)9876543210!/\1/
s/^\(...\)/\1!0000!0101!0202!0303!0404!0505!0606!0707!0808!0909!1102!1203!1304!1405!1506!1607!1708!1809!1910!2204!2305!2406!2507!2608!2709!2810!2911!3306!3407!3508!3609!3710!3811!3912!4408!4509!4610!4711!4812!4913!5510!5611!5712!5813!5914!6612!6713!6814!6915!7714!7815!7916!8816!8917!9918\
/
s/^\(.\)\(..\).*!\2\(..\).*\n/\1\3/
/^\(.\)0/{
s//\1/
b LP20011
}
s/\(.\)1/\10123456789a\
/
s/\(.\).*\1\(.\).*\n/\2/
s/a/10/
:LP20011
/[0-9];.$/b LP20009
s/;.*$//
s/^0\(.\)/\1/
:LP20010
G
s/^\([0-9]*\)\n\([0-9]*\);\(0*\)/\1\3;\2;\30/
h
s/^[0-9]*;//
x
s/^\([0-9]*\).*/\1/
# > ADD
# > CAT 
G
s/^\([0-9]*\)\n\([0-9]*\);.*/\1;\2;/
# < CAT
s/^/0;/
:LP20012
s/^\([0-9]*\);\([0-9]*\)\([0-9]\);\([0-9]*\)\([0-9]\);/\3\5\1;\2;\4;/
# W ATCH 1 PS
s/^\(...\)/\19876543210aaaaaaaaa;9876543210aaaaaaaaa;10a;/
s/\(.\)\(.\)\(.\)[0-9]*\1.\{9\}\(a*\);[0-9]*\2.\{9\}\(a*\);[0-9]*\3.\(a*\);/\4\5\6/
s/a\{10\}/b/
# W ATCH full1 PS
s/\(b*\)\(a*\)/\19876543210;\29876543210;/
# W ATCH full2 PS
s/.\{9\}\(.\)[0-9]*;.\{9\}\(.\)[0-9]*;/\1\2/
# W ATCH 2 PS
/;;/!b LP20012
/;;;/b LP20013
/^1/{
s/;;/;0;/
b LP20012
}
s/^0\([0-9]*\);\([0-9]*\);\([0-9]*\);/\2\3\1/
:LP20013
s/^0//
s/;;;//
:LP20014
# < ADD
G
s/\n[0-9]*//
/^[0-9]*;0*;[0-9]*;[0-9]/b LP20004
h
s/^[0-9]*;0*;[0-9]*;;//
x
s/;.*$//
s/^0*\(.\)/\1/
# < MUL
# > DROP
x
s/^[^;]*;//
x
# < DROP
# > SET $r
x
s/;$r;[0-9]\+//
G
s/\n/;$r;/
x
# < SET
# print  $i;
# > GET $i
g
/;$i;/!{
s/.*/$i/
b erudv
}
s/^.*;$i;\([0-9]*\).*/\1/
# < GET
# > OUT
p
# < OUT
# print  $r;
# > GET $r
g
/;$r;/!{
s/.*/$r/
b erudv
}
s/^.*;$r;\([0-9]*\).*/\1/
# < GET
# > OUT
p
# < OUT
# $i  = $i + 1;
# > GET $i
g
/;$i;/!{
s/.*/$i/
b erudv
}
s/^.*;$i;\([0-9]*\).*/\1/
# < GET
# > INC
s/$/+/
:LP20015
s/9+/+0/
t LP20015
s/^+/0+/
s/$/!0+1+2+3+4+5+6+7+8+9/
s/\(.+\)\([0-9]*\)!.*\1\(.\).*/\3\2/
# < INC
# > SET $i
x
s/;$i;[0-9]\+//
G
s/\n/;$i;/
x
# < SET
# > JUMP LP10000
b LP10000
# < JUMP
:LP10001
q
:erudv
s/^/CWS : Undefined variable : /
p
q
:erils
s/.*/CWS : Illegal substraction/
p
q
:erild
s/.*/CWS : Illegal division/
p
q