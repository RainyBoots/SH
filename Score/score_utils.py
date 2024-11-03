import xml.etree.ElementTree as ET
import verovio
import re
import os
from music21 import converter, instrument
import warnings
import hashlib
from dotenv import load_dotenv


resource_path = os.getenv("VEROVIO_RESOURCE_PATH")
load_dotenv()

def load_xml(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    return tree, root



def update_musicxml_file(xml_file_path, tree, root):
    for credit in root.findall('.//credit-words'):
        if 'default-y' in credit.attrib:
            current_value = float(credit.attrib['default-y'])
            new_value = current_value * 0.1 if current_value >= 1000 else current_value
            credit.attrib['default-y'] = str(new_value)

    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)



def create_envelope(instance):
    verovio.setDefaultResourcePath(resource_path)
    tk = verovio.toolkit()
    tk.setOptions({
        "header": "auto",
        "footer": 'none',
        "font": "Leland",
        "svgViewBox": "true",
        "justifyVertically": "true"

    })

    with open(instance.score.path, 'r', encoding='utf-8') as file:
        tk.loadData(file.read())

    svg_output = tk.renderToSVG()

    return svg_output



def sanitize_filename(filename):
       """
       Очищает имя файла, удаляя недопустимые символы.
       """
       sanitized = re.sub(r'[^a-zA-Z0-9 .\-—]', '', filename)
       return sanitized


def add_work_title(xml_file_path, tree, root):
    credit = root.find('credit[credit-type="title"]/credit-words')
    title = credit.text.strip() if credit is not None else None
    if title:
        work = ET.Element('work')
        work_title = ET.SubElement(work, 'work-title')
        work_title.text = title
        first_credit = root.find('identification')
        if first_credit is not None:
            index = list(root).index(first_credit)
            root.insert(index, work)
        else:
            root.append(work)
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)



def add_credits(xml_file_path, tree, root, credit_types):
    for credit_type in credit_types:
        credits = root.findall(f'credit[credit-type="{credit_type}"]/credit-words')

        if credits:
            identification = root.find(".//identification")

            if identification is not None:
                for credit in credits:
                    creator_name = credit.text.strip() if credit.text else None

                    if creator_name:
                        existing_creators = identification.findall(f'creator[@type="{credit_type}"]')
                        if not existing_creators:
                            creator_element = ET.SubElement(identification, "creator", type=credit_type)
                            creator_element.text = creator_name

    try:
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        print(f"Файл '{xml_file_path}' успешно обновлён.")
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")

def can_add_credits(root, credit_types):
    identification = root.find(".//identification")
    if identification is None:
        return True

    for credit_type in credit_types:
        credits = root.findall(f'credit[credit-type="{credit_type}"]/credit-words')
        if credits:
            for credit in credits:
                creator_name = credit.text.strip() if credit.text else None
                if creator_name:
                    existing_creators = {creator.text for creator in identification.findall(f'creator[@type="{credit_type}"]')}
                    if creator_name not in existing_creators:
                        return True

    return False

def manage_xml_operations(xml_file_path, credit_types):
    tree, root = load_xml(xml_file_path)
    work_title_present = root.find(".//work/work-title") is not None
    movement_title_present = root.find(".//movement-title") is not None
    
    if not (work_title_present or movement_title_present):
        add_work_title(xml_file_path, tree, root)
    
    if can_add_credits(root, credit_types):
        add_credits(xml_file_path, tree, root, credit_types)
    needs_update = False
    for credit in root.findall('.//credit-words'):
        if 'default-y' in credit.attrib and float(credit.attrib['default-y']) >= 1000:
            needs_update = True
            break

    if needs_update:
        update_musicxml_file(xml_file_path, tree, root)



def extract_instruments_from_musicxml(musicxml_path):
    warnings.filterwarnings('ignore')
    instrument_names = set()
    score = converter.parse(musicxml_path)
    for part in score.parts:
        instrument_name = part.getInstrument().instrumentName
        if 'Grand Piano' in instrument_name:
            instrument_name = 'Piano'
        instrument_name = re.sub(r'[(){}\[\]0-9]', '', instrument_name).strip() 
        instrument_names.add(instrument_name)
    return instrument_names


def count_parts_and_update_score(file_path):
    warnings.filterwarnings('ignore')
    score = converter.parse(file_path)


    instrument_names = set()
    for part in score.parts:
        instrument = part.getInstrument()
        if instrument and instrument.partId: 
            instrument_names.add(instrument.partId)

    part_count = len(instrument_names)
    return part_count


def calculate_page_count(file_path):
    verovio.setDefaultResourcePath(resource_path)
    tk = verovio.toolkit()
    tk.setOptions({
        "pageWidth": 2100,
        "pageHeight": 2970,
        "scale": 40,
        "breaks": "encoded",  
        "spacingSystem": 12,
        "spacingStaff": 12
    })
    with open(file_path, 'r', encoding='utf-8') as f:
        musicxml_content = f.read()
        tk.loadData(musicxml_content)
        page_count = tk.getPageCount()
    return int(page_count)

def get_family_data():
    from .models import Family_of_instruments
    families = Family_of_instruments.objects.prefetch_related('instruments').all()
    result = []

    for family in families:
        family_data = {
            'family_name': family.name,
            'instruments': []
        }

        instruments = family.instruments.all()
        for instrument in instruments:
            family_data['instruments'].append({
                'instrument_name': instrument.name,
                'instrument_id': instrument.id,  
            })

        result.append(family_data)
    return result

def get_instruments_by_voice():
    from .models import Instrument

    instruments_in_voice_family = Instrument.objects.filter(group__name='Voice')
    instrument_names = {instrument.name for instrument in instruments_in_voice_family}

    return instrument_names


def find_families_of_instruments(instruments):
    families_data = get_family_data()

    family_dict = {}
    for family in families_data:
        family_name = family['family_name']
        family_instruments = {instr['instrument_name'] for instr in family['instruments']}
        family_dict[family_name] = family_instruments

    found_families = set()

    for instrument in instruments:
        for family_name, family_instruments in family_dict.items():
            if instrument in family_instruments:
                found_families.add(family_name)

    return found_families if found_families else set()

def extract_list_instruments_from_musicxml(musicxml_path):
    warnings.filterwarnings('ignore')
    instrument_names = []
    score = converter.parse(musicxml_path)
    for part in score.parts:
        instrument_name = part.getInstrument().instrumentName       
        if 'Grand Piano' in instrument_name:
            instrument_name = 'Piano'
        instrument_name = re.sub(r'[(){}\[\]0-9]', '', instrument_name).strip()
        
        instrument_names.append(instrument_name)

    return instrument_names

    
def get_instruments_and_part_counts(file_path, part_count):
    score = converter.parse(file_path)
    instruments = extract_list_instruments_from_musicxml(file_path)
    parts = []
    for part in score.parts:
        inst = part.getInstrument()
        if inst:
            parts.append(inst.partId)
    instruments_set = set(instruments)
    found_families = find_families_of_instruments(instruments_set)
    print(instruments)
    print(parts)
    if part_count==1:
        return "Solo"
    elif instruments_set.issubset({"Piano"}):
        match part_count:
            case 2:
                if len(parts) == 4 and len(instruments) == 4:
                    return "Piano Four Hand"
                else:
                    return "Piano Duo"
            case 3:
                return "Piano Trio"
            case 4:
                return "Piano Quartet"
            case 5:
                return "Piano Quintet"
            case 6:
                return "Piano Sextet"
    elif found_families.issubset({"Bowed string", "Strings Plucked"}):
        match part_count:
            case 2:
                return "String Duet"
            case 3:
                return "String Trio"
            case 4:
                return "String Quartet"
            case 5:
                return "String Quintet"
            case 6:
                return "String Sextet"  
            case _ if part_count > 6:  
                return "String Ensemble"
    elif found_families.issubset({"Percussion Wood", "Percussion Metal", "Percussion Drum", "Percussion - Body"}):
        match part_count:
            case 2:
                return "Percussion Duet"
            case 3:
                return "Percussion Trio"
            case 4:
                return "Percussion Quartet"
            case 5:
                return "Percussion Quintet"
            case _ if part_count > 5:
                return "Percussion Ensemble"
    elif found_families.issubset({"Voice"}):
        if instruments_set.issubset({"Female"}):
            return "Women’s Choir"
        elif instruments_set.issubset({"Male"}):
            return "Men’s Choir"
        elif instruments_set.issubset({"Soprano", "Alto", "Tenor", "Baritone", "Bass", "Voice"}):
            return "SATB"
        elif instruments_set.issubset(get_instruments_by_voice()):
            return "Choir"
    elif found_families.issubset({"Woodwinds"}):
        match part_count:
            case 2:
                return "Woodwind Duet"
            case 3:
                return "Woodwind Trio"
            case 4:
                return "Woodwind Quartet"
            case 5:
                return "Woodwind Quintet"
    elif instruments_set.issubset({"Bass Saxophone", "Soprano Saxophone", "Baritone Saxophone", "Tenor Saxophone", "Alto Saxophone"}):
        return "Saxophone Ensemble"
    elif found_families.issubset({"Brass"}):
        match part_count:
            case 2:
                return "Brass Duet"
            case 3:
                return "Brass Trio"
            case 4:
                return "Brass Quartet"
            case 5:
                return "Brass Quintet"
            case _ if part_count > 5:
                return "Brass Ensemble"
    elif 2 <= len(instruments) <=5:
        match part_count:
            case 2:
                return "Mixed Duet"
            case 3:
                return "Mixed Trio"
            case 4:
                return "Mixed Quartet"
            case 5:
                return "Mixed Quintet"
    elif found_families.issubset({"Woodwinds", "Percussion Wood", "Percussion Metal", "Percussion Drum", "Percussion - Body", "Brass"}):
        return "Concert Band"
    elif 5 < part_count < 20:
        return "Chamber Orchestra"
    elif part_count >= 20:
        return "Symphony Orchestra"
    else:
        return ""
    
def get_key(file_path):
    score = converter.parse(file_path)
    key_signatures = score.flatten().getElementsByClass('KeySignature')
    first_key = key_signatures[0].asKey().name
    return first_key

def get_measures(file_path):
    score = converter.parse(file_path)
    parts = score.parts
    total_measures = len(parts[0].getElementsByClass('Measure'))
    return total_measures

HASH_ALGORITHM = 'sha256'
def calculate_file_hash(file, algorithm=HASH_ALGORITHM):
    hash_obj = getattr(hashlib, algorithm)()
    file.seek(0)
    for chunk in iter(lambda: file.read(1024 * 1024), b''):
        hash_obj.update(chunk)
    file.seek(0)
    return hash_obj.hexdigest()





        

    
        

