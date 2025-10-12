class BasicIO:
    @staticmethod
    def read_txt(filename):
        with open(filename) as f:
            lines = f.readlines()
        return lines

    @staticmethod
    def read_as_block(filename):
        ret = ""
        for s in BasicIO.read_txt(filename):
            ret += s + "\n"
        return ret
