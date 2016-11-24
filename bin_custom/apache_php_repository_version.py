#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import check_output

def busca_apache_php():
    pakete = "libapache2-mod-php"
    paketes = []

    found = check_output("aptitude search libapache2-mod-php", shell=True).split("\n")

    for cosa in found[:-1]:
        if not cosa.split("libapache2-mod-php")[1][0].startswith(" "):
            if not ":" in cosa:
                candidato = cosa[4:].split()[0]
                if candidato[-1].isdigit():
                    paketes.append(cosa[4:].split()[0])

    paketes.sort()

    if paketes:
        return paketes[-1]
    else:
        return pakete

if __name__ == "__main__":
    print busca_apache_php()


