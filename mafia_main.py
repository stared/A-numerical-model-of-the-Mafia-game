# Bez polskich znakow, please!
# Cokolwiek robimy staramy sie nazywac przejrzyscie (tj. raczej 'wykres_wykladnika_od_spostrzegawczosci" niz "wyk4"),
# a takze obficie i rzetelnie komentujemy.

# n  -  aktualna liczba wszystkich graczy
# m  -  aktualna liczba mafiozow

# Do czego ma sluzyc:
# - numerycznego modelowania gry w mafie w oparciu o rozne proste modele wymiany informcacji i glosowania
# - dodawania Kataniego i Kurtyzany
# - raczej do gry bez odkrywania kart jak ktos zginie (modelowanie z odkrywaniem byloby trudniejsze
# bo byloby znacznie wiecej czesc i taktycznej itd)

# Importujemy to czy owo. Najlepiej bez fraz 'from costam import *', co przy dluzszym projekcie moga
# przypadkiem sie pojawic rzeczy o tej samej nazwie z innych modulow, a tego nie chcemy.

import numpy as np
import random



#
# STRATEGIE I MOZLIWE DZIALANIA W DZIEN I W NOCY
#


# generuj_postacie
# Funkcja zwracajaca liste literek, odpowiadajacych typom postaci.
# Standardowo 'm' to mafioza, 'c' to zwykly miastowy, 'k' to Katani a 'd' to martwy.

def mafia_i_miastowi( n, m, **dod_arg ):
    return (['m'] * m) + (['c'] * ( n - m ))
    
def mafia_i_miastowi_z_katanim( n, m, **dod_arg ):
    return (['m'] * m) + (['c'] * ( n - m - 1)) + ['k']
    

# faza_dyskusji
# w czasie fazy dyskusji dochodzi do zmiany podejrzen - zarowno analizy porzedniego linczu, tego kto zostal zabity w nocy, obserwacji, jak i - wymiany informacji
# kto_kogo_podejrzewa[i][j] - jak bardzo i-ty gracz chce ubic j-tego

# kazdy losowo podejrzewa, inaczej w kazdej turze
def losowe_podejrzenia( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, ostatnio_zabity,  **dodatkowe_argumetny):
    for i in range( len( kto_kogo_podejrzewa ) ):
        for j in range( len( kto_kogo_podejrzewa ) ):
            if (kto_jest_kim[i] != 'd') and (kto_jest_kim[j] != 'd'): # martwi nie glosuja, na martwych sie nie glosuje
                kto_kogo_podejrzewa[i][j] = random.random()
            else:
                kto_kogo_podejrzewa[i][j] = 0

def obserwacja( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, ostatnio_zabity,
spostrzegawczosc = 1., udawana_spostrzegawczosc_mafii = 0., **dodatkowe_argumetny ):
    for i in range( len( kto_kogo_podejrzewa ) ):
        if kto_jest_kim[i] == 'm':
            for j in range( len( kto_kogo_podejrzewa ) ):
                if kto_jest_kim[j] == 'm':
                    kto_kogo_podejrzewa[i][j] += (1 + (udawana_spostrzegawczosc_mafii / n)) * random.random()
                elif kto_jest_kim[j] != 'd':  #zakladamy implicite, ze dodatkowe postacie sa z miasta
                    kto_kogo_podejrzewa[i][j] += 1 * random.random()
        elif kto_jest_kim[i] != 'd': #zakladamy implicite, ze dodatkowe postacie sa z miasta
            for j in range( len( kto_kogo_podejrzewa ) ):
                if kto_jest_kim[j] == 'm':
                    kto_kogo_podejrzewa[i][j] += (1 + (spostrzegawczosc / n)) * random.random()
                elif kto_jest_kim[j] != 'd':  #zakladamy implicite, ze dodatkowe postacie sa z miasta
                    kto_kogo_podejrzewa[i][j] += 1 * random.random()        

# faza_linczowania
# w czasie fazy linczowania gracze oddaja glos 
# - czy gracze glosuja 'za glosem serca' czy tez np sa wysuwane 3 kandydatury i sie do nich dostosowuja, czy np. gracze staraja sie akumulowac glosy
# - jak przekladaja sie glosy na zabijanie (mozna rozwazyc np. model gdzie w razie remisu nikt nie ginie)

def proste_linczowanie( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, **dodatkowe_argumetny ):
# kazdy glosuje zgodnie z preferencjami, w przypadku remisu ginie losowa osoba z remisujacych
    kto_na_kogo_glosowal = np.zeros( [ len(kto_jest_kim) ], int ) - 1
    glosy_na_dana_osobe = np.zeros( [ len(kto_jest_kim) ], int )
    for i in range( len( kto_jest_kim ) ):
        if kto_jest_kim[i] != 'd': # kazdy zywy glosuje
            kto_na_kogo_glosowal[i] = kto_kogo_podejrzewa[i].argmax()
            glosy_na_dana_osobe[ kto_na_kogo_glosowal[i] ] += 1
    # teraz bawimy sie remisem
    max_glosow = max( glosy_na_dana_osobe )
    zwyciezcy = list( i for i in range( len( glosy_na_dana_osobe )) if glosy_na_dana_osobe[i] == max_glosow )
    ostatnio_zlinczowany = random.sample( zwyciezcy, 1 )[0]
    # a teraz outcome
    if kto_jest_kim[ ostatnio_zlinczowany ] == 'm':
        m += -1
    kto_jest_kim[ ostatnio_zlinczowany ] = 'd'
    return ( n - 1, m, ostatnio_zlinczowany )
        

# faza_nocna
# W czasie niej mafia zabija swoja ofiare i dzialaja inne ewentualne frakcje nocne. 
# Zmienia n,m, kto_jest_kim (bo ktos zwykle 'sie' przekreca) i ew. tabele podejrzanosci, np. w przypadku gdy Katani sprawdza
def mafia_zabija_losowego_miastowego( n, m, kto_jest_kim, kto_kogo_podejrzewa, **dodatkowe_argumetny ):
    numerki_miastowych = list( i for i in range( len( kto_jest_kim )) if ( (kto_jest_kim[i] != 'm') and (kto_jest_kim[i] != 'd') ) )
    # ^ znow zakladamy implicite, ze nie-mafiozi to miastowi
    ostatnio_zabity = random.sample( numerki_miastowych, 1)[0]
    kto_jest_kim[ ostatnio_zabity ] = 'd'
    return (n - 1, m, ostatnio_zabity )



#
# GLOWNA FUNKCJA
#


# Glowna funkcja przeprowadzajace gre w mafie. Jesli chcesz zrobic funkcje zwracajaca jako wynik np.
# log z podejrzen, albo liczebnosci mafiozow (czy tez cokolwiek wypisujaca w czasie rzeczywistym),
# zrob osobna funkcje.

def kto_wygral_jedna_gre( n_poczatkowe , m_poczatkowe,
generuj_postacie = mafia_i_miastowi, faza_dyskusji = losowe_podejrzenia,
faza_linczowania = proste_linczowanie, faza_nocna = mafia_zabija_losowego_miastowego,
wypisuj = False, **dodatkowe_argumetny):
    n = n_poczatkowe
    m = m_poczatkowe
    kto_jest_kim = generuj_postacie( n_poczatkowe , m_poczatkowe, **dodatkowe_argumetny)
    if wypisuj:
        print kto_jest_kim
    kto_kogo_podejrzewa = np.zeros( [n_poczatkowe, n_poczatkowe] )
    # kto_kogo_podejrzewa[i][j] - jak bardzo i-ty gracz chce ubic j-tego
    kto_na_kogo_glosowal = np.zeros( [n_poczatkowe], int ) - 1 # na i-ym miejscu jest glos i-tej osoby
    ostatnio_zabity = -1
    # ^ ostatnio nikt nie byl zabity wiec dajemy -1
    while n > m:
        faza_dyskusji( n, m, kto_jest_kim, kto_kogo_podejrzewa,kto_na_kogo_glosowal, ostatnio_zabity,  **dodatkowe_argumetny)
        # ^ modyfikuje tylko kto_kogo_podejrzewa
        ( n, m, ostatnio_zlinczowany ) = faza_linczowania( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, **dodatkowe_argumetny )
        # ^ modyfikuje tylko n, m, ostatnio_zlinczowany i kto_jest_kim
        if wypisuj:
            print ostatnio_zlinczowany, 'zostal zlinczowany.'
        if ( m == 0 or n - m == 0 ):
            break
        ( n, m, ostatnio_zabity ) = faza_nocna( n, m, kto_jest_kim, kto_kogo_podejrzewa, **dodatkowe_argumetny )
        # ^ modyfikuje n, m, kto_jest_kim, ostatnio_zabity i kto_kogo_podejrzewa (to ostatnie w przypadku np. Kataniego)
        if wypisuj:
            print ostatnio_zabity, 'zostal zamordowany.'
    if m > 0:
        if wypisuj:
            print 'Wygrala mafia!'
        return 1
    else:
        if wypisuj:
            print 'Wygrali miastowi!'
        return 0



#
# SKANOWANIE, WYKRESLANIE ITD
#


def skanuj_dla_jednego_mafiozo( n_min, n_max, ile_razy, **argumenty):
    return list(
    [ n, sum( list( kto_wygral_jedna_gre( n, 1, **argumenty) for i in range( ile_razy) ) ) / float( ile_razy ) ]
    for n in range(n_min, n_max + 1)
    )


# TO DO:
# - dopasowanie w(n,m) = stala n^gamma, wraz z niepewnosciami
# - wykreslanie wynikow, wraz z dopasowaniem i stosownymi podpisami
# - skanowanie gamm dla roznych spostrzegawczosci, a takze wykreslanie tego
# - inne strategie w ciagu dnia i nocy, Katani, ...
# - cala pula innych pomyslow :)


