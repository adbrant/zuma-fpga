##find a string between two strings.
#return the string or None
def find_substring( s, first, last ):
    try:
        start = s.find( first ) + len( first )
        end = s.find( last, start )
        if start >= 0 and end >= 0:
            return s[start:end]
        else:
            return None
    except ValueError:
        return None