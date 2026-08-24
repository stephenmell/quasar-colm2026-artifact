import termcolor

from .env import *

ColoredStringChunk : TypeAlias = Tuple[Optional[str], str]
ColoredString : TypeAlias = Tuple[ColoredStringChunk, ...]

ColoredStringChunkIndex : TypeAlias = Tuple[int, int]
# (i, j), j must be *inside* the i-th str, i.e. j < len(cs[i][1])
# i can be = len(cs) if j = 0 (representing past end of entire string)

ColoredLines : TypeAlias = Tuple[ColoredString, ...]

def cs_ansi(cs : ColoredString) -> str:
    return "".join(
        s if c is None else termcolor.colored(s, c, force_color=True)
        for c, s in cs
    )

def cs_cat(*args : Union[str, ColoredString]) -> ColoredString:
    ret : List[ColoredStringChunk] = []
    for arg in args:
        if isinstance(arg, str):
            ret.append((None, arg))
        else:
            ret.extend(arg)
    return tuple(ret)

def cs_join(delim : Union[str, ColoredString], css : Iterable[Union[str, ColoredString]]) -> ColoredString:
    css2 : List[Union[str, ColoredString]] = []
    for i, arg in enumerate(css):
        if i > 0:
            css2.append(delim)
        css2.append(arg)
    return cs_cat(*css2)

def cs_len(cs : ColoredString) -> int:
    return sum(len(s) for _c, s in cs)

def cs_index_to_chunk_index(cs : ColoredString, i : int) -> ColoredStringChunkIndex:
    dist_to_i = i
    for i, (_c, s) in enumerate(cs):
        if dist_to_i < len(s):
            return i, dist_to_i
        else:
            dist_to_i -= len(s)
    if dist_to_i == 0:
        return len(cs), 0
    else:
        raise IndexError

def cs_substring(cs : ColoredString, i : int, j : int) -> ColoredString:
    assert i <= j, (i, j)
    i_chunk, i_offset = cs_index_to_chunk_index(cs, max(i, 0))
    j_chunk, j_offset = cs_index_to_chunk_index(cs, min(j, cs_len(cs)))
    ret : List[ColoredStringChunk] = []
    for chunk_index in range(i_chunk, j_chunk + 1):
        if chunk_index == len(cs):
            assert j_offset == 0
            break
        chunk_color, chunk_str = cs[chunk_index]
        start_offset = i_offset if chunk_index == i_chunk else 0
        end_offset = j_offset if chunk_index == j_chunk else len(chunk_str)
        ret.append((chunk_color, chunk_str[start_offset:end_offset]))
    return tuple(ret)

IndentedLinesItem : TypeAlias = Union[
    Tuple[Literal["str"], ColoredString],
    Tuple[Literal["block"], "IndentedLines"],
]
IndentedLines : TypeAlias = Tuple["IndentedLinesItem", ...]

INDENTATION_STR : str = "  "
WRAP_STR : str = "⤷ "

def il_len(il : IndentedLines) -> int:
    return sum(ili_len(ili) for ili in il)

def ili_len(ili : IndentedLinesItem) -> int:
    match ili:
        case "str", _s:
            return 1
        case "block", b:
            return il_len(b)


def il_pair_pad_end(a : IndentedLines, b : IndentedLines) -> Tuple[IndentedLines, IndentedLines]:
    a_len = il_len(a)
    b_len = il_len(b)
    longest = max(a_len, b_len)
    a_gap = longest - a_len
    b_gap = longest - b_len
    a_padding : IndentedLines = (("str", cs_cat()),) * a_gap
    b_padding : IndentedLines  = (("str", cs_cat()),) * b_gap
    return a + a_padding, b + b_padding

def il_as_lines(x : IndentedLines, indentation : int = 0) -> ColoredLines:
    return tuple(l
        for y in x
        for l in ili_as_lines(y, indentation)
    )
def ili_as_lines(x : IndentedLinesItem, indentation : int) -> ColoredLines:
    match x:
        case "str", s:
            return (cs_cat("".join((INDENTATION_STR,) * indentation), s),)
        case "block", b:
            return il_as_lines(b, indentation + 1)

def cl_print(cl : ColoredLines):
    for cs in cl:
        print(cs_ansi(cs))

def word_wrap_cl(lines : ColoredLines, width : int) -> ColoredLines:
    return tuple(
        physical_line
        for virtual_line in lines
        for physical_line in word_wrap_cl_chunker(virtual_line, width)
    )

def word_wrap_cl_chunker(cs : ColoredString, width : int) -> ColoredLines:
    ret : List[ColoredString] = []
    i = 0
    while i < cs_len(cs):
        is_first = len(ret) == 0
        chunk_size = width if is_first else width - len(WRAP_STR)
        i2 = i + chunk_size
        if is_first:
            ret.append(cs_substring(cs, i, i2))
        else:
            ret.append(cs_cat(WRAP_STR, cs_substring(cs, i, i2)))
        i = i2
    if len(ret) == 0:
        ret.append(cs_cat())
    final_line_gap = width - cs_len(ret[-1])
    if final_line_gap > 0:
        ret[-1] = cs_cat(ret[-1], "".join((" ",) * final_line_gap))
    return tuple(ret)

def padding_line(width : int) -> ColoredString:
    return cs_cat("".join((" ",) * width))

def word_wrap_multi_cl_chunker(lineses_and_widths : Tuple[Tuple[ColoredLines, int], ...],) -> Tuple[Tuple[ColoredString, ...], ...]:
    virtual_line_count = max((len(lines) for lines, _width in lineses_and_widths), default = 0)
    ret : List[Tuple[ColoredString, ...]] = []
    for i in range(virtual_line_count):
        physical_lineses : List[ColoredLines] = [] # list of length num_cols
        for lines, width in lineses_and_widths:
            line = lines[i] if i < len(lines) else padding_line(width)
            physical_lineses.append(word_wrap_cl_chunker(line, width))
        physical_line_count = max((len(lines) for lines in physical_lineses), default = 0)
        for j in range(physical_line_count):
            composite_line = tuple(lines[j] if j < len(lines) else padding_line(lineses_and_widths[k][1]) for k, lines in enumerate(physical_lineses))
            ret.append(composite_line)
    
    return tuple(ret)

def word_wrap_multi_cl_twocolumn(lines_left : ColoredLines, lines_right : ColoredLines, width : int, delimiter : ColoredString) -> ColoredLines:
    col_width = (width - cs_len(delimiter))//2
    return tuple(
        cs_cat(left, delimiter, right)
        for left, right in word_wrap_multi_cl_chunker(((lines_left, col_width), (lines_right, col_width)))
    )
