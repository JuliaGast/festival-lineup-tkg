from rdflib import Graph, Namespace, Literal, RDF
from rdflib.namespace import XSD
import requests
import time
import json
import copy
from urllib.parse import quote

from rdflib import URIRef, RDFS
# -------------------------
# Namespaces
# -------------------------

EX = Namespace("https://tkgconcertevaluation.org/relation/")

MB_ARTIST = Namespace("https://musicbrainz.org/artist/")
MB_RELEASE = Namespace("https://musicbrainz.org/release-group/")
MB_LABEL = Namespace("https://musicbrainz.org/label/")
MB_GENRETAG = Namespace("https://musicbrainz.org/tag/") #genretag
MB_AREA = Namespace("https://musicbrainz.org/area/")

FALLBACK_AREA = Namespace("https://tkgconcertevaluation.org/area/") #fallback area for unknown areas
EX_TYPE = Namespace("https://tkgconcertevaluation.org/type/")

SL_VENUE = Namespace("https://www.setlist.fm/venue/")
SL_FESTIVAL = Namespace("https://www.setlist.fm/festival/")



g = Graph()
g.bind("ex", EX)

# -------------------------
# Relation mapping (your 23 relations)
# -------------------------

RELATION_MAP = {
    "performs_concert_at": EX.performsConcertAt,
    "performs_at_festival": EX.performsAtFestival,
    "happens_in_venue": EX.happensInVenue,

    "releases_album": EX.releasesAlbum,
    "releases_ep": EX.releasesEP,

    "has_genre": EX.hasGenre,

    "venue_has_location": EX.venueHasLocation,
    "location_has_country": EX.locationHasCountry,

    "has_begin_area": EX.hasBeginArea,
    "has_area": EX.hasArea,
    "has_type": EX.hasType,

    "label_founder": EX.labelFounder,
    "recording_contract": EX.recordingContract,
    "personal_label": EX.personalLabel,
    "artists_and_repertoire_position_at": EX.artistAndRepertoirePositionAt,
    "personal_publisher": EX.personalPublisher,
    "owner": EX.owner,
    "producer_position_at": EX.producerPositionAt,
    "creative_position_at": EX.creativePositionAt,
    "executive_position_at": EX.executivePositionAt,
    "engineer_position_at": EX.engineerPositionAt,
    "named_after_label": EX.namedAfterLabel,
    "named_after_artist": EX.namedAfterArtist,
    
}

def shorten(uri, prexies):
    return f"<{uri}>"


def get_area_uri(name, area_dict):
    """Resolve area string → MusicBrainz URI or fallback"""
    key = name.strip().lower()
    if 'klanx' in key:
        a=1
    if key in area_dict:
        uri = area_dict.get(key, None)['uri']
        if uri == None: 
            key = quote(key.replace(" ", "_"), safe="")
            return FALLBACK_AREA[key]            
        else:
            return uri
    else:
        key = quote(key.replace(" ", "_"), safe="")
        return FALLBACK_AREA[key]
            





# -------------------------
# Entity routing (CORE LOGIC)
# -------------------------
festivals_nounique = set()
def uri_for_entity(entity_id, entity_type, area_dict, festival_info, entityid2string_dict):
    """
    Maps (id, type) → correct URI namespace
    """

    entity_orig = copy.copy(entity_id)
    

    if entity_type == "artist":
        entity_id = quote(entity_id, safe="")
        return MB_ARTIST[entity_id]

    if entity_type == "release":
        entity_id = quote(entity_id, safe="")
        return MB_RELEASE[entity_id]

    if entity_type == "label":
        entity_id = quote(entity_id, safe="")
        return MB_LABEL[entity_id]

    if entity_type == "area":
        area_uri =  get_area_uri(entity_id, area_dict)
        return area_uri

    if entity_type == "venue":
        venue_string = entityid2string_dict.get(entity_orig, entity_id)
        try:
            if 'FESTIVAL' in venue_string:
                venue_uripart = 'unknown'
                festivals_nounique.add((venue_string, entity_orig, entity_id))
            else:
                venue_uripart = venue_string.split("VENUE:", 1)[1].split(".html", 1)[0]
                if 'venue/' in venue_uripart:
                    venue_uripart = venue_uripart.split('venue/', 1)[1]
                if len(venue_uripart) < 1:
                    venue_uripart = 'unknown'
            if 'html' in venue_uripart:
                venue_uripart = venue_uripart.split('.html', 1)[0]
            else:
                venue_uripart = venue_uripart + '-' + entity_orig
        except Exception:
            venue_uripart = entity_id
            print(f"WARNING: Could not extract venue slug from venue string {venue_string}. Using entity_id as fallback.")

        venue_uripart = quote(venue_uripart, safe="")
        return SL_VENUE[venue_uripart]

    if entity_type == "festival":
        fest = festival_info.get(entity_orig, None)
        festival_url = fest['general_info'].get("festival_url", None) if fest else None
        if festival_url is None:
            print(f"WARNING: Festival {entity_orig} not found in festival_info. ")
        else:
            # extract slug between 'festivals/' and '.html'
            try:
                festival_uripart = festival_url.split("festivals/", 1)[1].split(".html", 1)[0]
            except Exception:
                festival_uripart = entity_id
                print(f"WARNING: Could not extract festival slug from URL {festival_url}. Using entity_id as fallback.")
        festival_uripart = quote(festival_uripart, safe="")
        return SL_FESTIVAL[festival_uripart]
    
    if entity_type == "genre":
        entity_id = quote(entity_id, safe="")
        return MB_GENRETAG[entity_id]
    
    if entity_type == "type":
        entity_id = quote(entity_id, safe="")
        return EX_TYPE[entity_id]
    


    # fallback
    print(f"MAPPING DID NOT WORK: WARNING, {entity_id} of type {entity_type} not found in any namespace.")
    return None


def parse_genre(value):
    return MB_GENRETAG[value] #.strip().lower().replace(" ", "_")]




# -------------------------
# RDF-star quad generator
# -------------------------

def make_rdf_star(subject, relation, obj, year, prefixes):
    pred = RELATION_MAP[relation]

    return (
        f"<< {shorten(subject, prefixes)} {shorten(pred, prefixes)} {shorten(obj, prefixes)} >> "
        f"{shorten(EX.year, prefixes)} \"{year}\"^^{shorten('http://www.w3.org/2001/XMLSchema#Year', prefixes)} ."
    )


# -------------------------
# Main line processor
# -------------------------

def process_line(line, type_lookup, area_dict, timestamp_dict, prefixes, festival_info, entityid2string_dict):
    """
    Format:
    subject_id,relation,object_id,year
    """

    year, s_id, o_id, rel = line.strip().split(",")
    year = timestamp_dict.get(year, year)  # fallback to original if not found
    s_type, o_type = type_lookup.get(rel, ("unknown", "unknown"))


    subject = uri_for_entity(s_id, s_type, area_dict, festival_info, entityid2string_dict)
    obj = uri_for_entity(o_id, o_type, area_dict, festival_info, entityid2string_dict)

    if subject is None or obj is None:
        print(f"WARNING: Could not resolve subject or object for line: {line.strip()}")



    return make_rdf_star(subject, rel, obj, year, prefixes)


# -------------------------
# File converter
# -------------------------

def convert(input_file, output_file, type_lookup, area_dict, timestamp_dict, prefixes, festival_info, entityid2string_dict):
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:

        # # prefixes
        # for base, prefix in prefixes.items():
        #     out.write(f"@prefix {prefix}: <{base}> .\n")
        # out.write("\n")
        

        for line in f:

            if 'timestamp,head,tail,relation_type' in line:
                continue
            if not line.strip():
                continue
            if line.startswith("#"):
                continue

            try:
                rdf_line = process_line(line, type_lookup, area_dict, timestamp_dict, prefixes, festival_info, entityid2string_dict)
                out.write(rdf_line + "\n")

            except Exception as e:
                print(f"Skipping line: {line.strip()} ({e})")

        print(f"Conversion complete. Output written to {output_file}")


def make_label_rdf(entity2id_file, output_file_labels, area_dict):
    g_label = Graph()
    for id, string in entityid2string_dict.items():
        id = quote(id, safe="")
        if "ARTIST:" in string:
            string = string.split("ARTIST:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://musicbrainz.org/artist/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "FESTIVAL:" in string:
            string = string.split("FESTIVAL:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://www.setlist.fm/festivals/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "RELEASE:" in string:
            string = string.split("RELEASE:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://musicbrainz.org/release-group/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "LABEL:" in string:
            string = string.split("LABEL:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://musicbrainz.org/label/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "TYPE:" in string:
            string = string.split("TYPE:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://tkgconcertevaluation.org/type/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "GENRE_TAG:" in string:
            string = string.split("GENRE_TAG:", 1)[1].split(".html", 1)[0]
            g_label.add((URIRef(f"https://tkgconcertevaluation.org/genre/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "AREA:" in string:
            string = string.split("AREA:", 1)[1].split(".html", 1)[0]
            area_uri = get_area_uri(string, area_dict)
            g_label.add((URIRef(f"https://musicbrainz.org/area/{id}"), RDFS.label, Literal(string, datatype=XSD.string)))
        elif "VENUE:" in string:
            venue_uripart = string.split("VENUE:", 1)[1].split(".html", 1)[0]
            if 'venue/' in venue_uripart:
                venue_uripart = venue_uripart.split('venue/', 1)[1]
            if len(venue_uripart) < 1:
                venue_uripart = 'unknown'
            if 'html' in venue_uripart:
                venue_uripart = venue_uripart.split('.html', 1)[0]
            g_label.add((URIRef(f"https://www.setlist.fm/venue/{id}"), RDFS.label, Literal(venue_uripart, datatype=XSD.string)))

    g_label.serialize(destination=output_file_labels, format="nt")



if __name__ == "__main__":

    prefixes = { # not used
        "https://musicbrainz.org/artist/": "mba",
        "https://musicbrainz.org/release-group/": "mbr",
        "https://musicbrainz.org/label/": "mbl",
        "https://musicbrainz.org/area/": "mbarea",
        "https://musicbrainz.org/tag/": "mbtag",
        "https://www.setlist.fm/venue/": "slv",
        "https://www.setlist.fm/festival/": "slf",
        "https://tkgconcertevaluation.org/area/": "area",
        "https://tkgconcertevaluation.org/type/": "type",
        "http://www.w3.org/2001/XMLSchema#": "xsd",
        "https://tkgconcertevaluation.org/relation/": "rel",


    }


    type_lookup = {
        'performs_at_festival': ('artist', 'festival'),
        'happens_in_venue': ('festival', 'venue'),
        'performs_concert_at': ('artist', 'venue'),
        'venue_has_location': ('venue', 'area'),
        'location_has_country': ('area', 'area'),
        'releases_album': ('artist', 'release'),
        'releases_ep': ('artist', 'release'),
        'has_genre': ('release', 'genre'),
        'has_begin_area': ('artist', 'area'),
        'has_area': ('artist', 'area'),
        'has_type': ('artist', 'type'),
        'label_founder': ('artist', 'label'),
        'recording_contract': ('artist', 'label'),
        'personal_label': ('artist', 'label'),
        'artists_and_repertoire_position_at': ('artist', 'label'),
        'personal_publisher': ('artist', 'label'),
        'owner': ('artist', 'label'),
        'producer_position_at': ('artist', 'label'),
        'creative_position_at': ('artist', 'label'),
        'executive_position_at': ('artist', 'label'),
        'engineer_position_at': ('artist', 'label'),
        'named_after_label': ('artist', 'label'),
        'named_after_artist': ('artist', 'label')
    }

    area_file = './rdf/resolved_areas.json'
    with open(area_file, 'r', encoding='utf-8') as f:
        area_dict = json.load(f)

    timestamp_file = './rdf/timestamp2int.txt'
    with open(timestamp_file, 'r', encoding='utf-8') as f:
        timestamp_lines = [line.strip() for line in f if line.strip()]
        timestamp_dict = {line.split("\t")[0]: line.split("\t")[1] for line in timestamp_lines}


    festival_file = './rdf/very_large_festivals_info_germany.json'
    with open(festival_file, 'r', encoding='utf-8') as f:
        festival_info = json.load(f)

    entityid2string_dict ={}
    entity2id_file = './forecasting/tgb/datasets/tkgl_concert/entity2id.txt'
    with open(entity2id_file, 'r', encoding='utf-8') as f:
        entity_lines = [line.strip() for line in f if line.strip()]
        entityid2string_dict = {line.split("\t")[0]: line.split("\t")[1] for line in entity_lines}

    input_file = "./forecasting/tgb/datasets/tkgl_concert/tkgl-concert_edgelist.csv" 
    output_file = "./rdf/output.nt" 
    # input_file = "./rdf/input_small.csv"
    # output_file = "./rdf/output_small3.nt"

    convert(input_file, output_file, type_lookup, area_dict, timestamp_dict, prefixes, festival_info,entityid2string_dict)

    output_file_labels = output_file.replace(".nt", "_labels.nt")
