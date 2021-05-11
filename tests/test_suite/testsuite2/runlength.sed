:encode
  p
	/^$/ b decode
:start_e
	/^[0-9]/ b decode
	s/^/1/
:loop_e
	h
	/^9+([^0-9])\1+/ {
		s/^(9+).*/0\1/
		y/09/10/
		G
		s/^(.+)\n[0-9]+.(.*)/\1\2/
		b loop_e }
	/^[0-9]*[0-8]([^0-9])\1+/ {
		s/^[0-9]*([0-8]).*/\1/
		y/012345678/123456789/
		G
		s/^(.)\n([0-9]*)[0-8].(.*)/\2\1\3/
		b loop_e }
	/^[0-9]+9+([^0-9])\1+/ {
		s/^[0-9]*([0-8]9+).*/\1/
		y/0123456789/1234567890/
		G
		s/^(.+)\n([0-9]*)[0-8]9+.(.*)/\2\1\3/
		b loop_e }
	s/^([0-9]+.)(.*)/\2\1/
	b start_e

:decode
  p
	/^$/ b
:start_d
	/^[^0-9]/ b
:loop_d
	/^1[^0-9]/ {
		s/^1(.)(\1*)(.*)/\3\1\2/
		b start_d	}
	h
	/^[0-9]*[1-9][^0-9]/ {
		s/^[0-9]*([1-9]).*/\1/
		y/123456789/012345678/
		G
		s/^([0-8])\n([0-9]*)[1-9]([^0-9])(.*)/\2\1\3\3\4/
		b loop_d }
	/^[0-9]+0[^0-9]/ {
		s/^[0-9]*([1-9]0+)[^0-9].*/\1/
		y/0123456789/9012345678/
		G
		s/^([0-9]+)\n([0-9]*)[1-9]0+([^0-9])(.*)/\2\1\3\3\4/
		s/^0+//
		b loop_d }