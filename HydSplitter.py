from lxml import etree
import copy
import sys

if len(sys.argv) == 2:
    inputFile = sys.argv[1]
    outputFile = 'temp.h2song'
    print('Outputting to temp.h2song')
elif len(sys.argv) == 3:
    inputFile = sys.argv[1]
    outputFile = sys.argv[2]
else:
    print('Please enter python HydSplitter InputFile [OutputFile (temp.h2song)]')

resequencePatterns = True
if resequencePatterns:
    print('Resequence patterns is set to true. Note this does not work if there are overlapping patterns of different lengths (...but why would you do that)')

tree = etree.parse(inputFile)
root = tree.getroot()
patternList = root.find('patternList')
patternSequence = root.find('patternSequence')
newPatternList = etree.Element('patternList')
newPatternSequence = etree.Element('patternSequence') 

split_dict = {}

# Find all patterns with a size greater than 192
for pattern in patternList.iter('pattern'):
    # First append the original pattern to new pattern list
    newPatternList.append(pattern)

    # Now split into separate patterns if necessary
    name = pattern.find('name').text
    size = int(pattern.find('size').text)

    split_dict[name] = 1
    if (size > 192) and (size % 192 == 0):
        # We split the pattern into sub patterns
        totalSubPatterns = size/192
        split_dict[name] = totalSubPatterns

        for i in range(totalSubPatterns):
            # We now create a new pattern and attach it to patternList
            newPattern = etree.SubElement(patternList, 'pattern')

            # Add the name the size and the category
            newName = etree.SubElement(newPattern, 'name')
            newName.text = name + '_{}'.format(i)

            newSize = etree.SubElement(newPattern, 'size')
            newSize.text = '192'
            
            newCategory = etree.SubElement(newPattern, 'category')
            newCategory.text = 'not_categorized'

            # Now add the notes, adjusting for the fact they are offset by i*192
            newNotes = etree.SubElement(newPattern, 'noteList')

            for note in pattern.iter('note'):
                position = int(note.find('position').text)
                if (position >= i*192) and (position < (i+1)*192):
                    # The note fits in the current subPattern
                    convertedNote = copy.copy(note)

                    # Now adjust the position of the converted note to account for the pattern shift
                    convertedNote.find('position').text = str(position - i*192)
                    newNotes.append(convertedNote)

            # Finally append the newPattern to the newPatternList
            newPatternList.append(newPattern)

# We now loop through the pattern sequence, replacing any instances of the pattern with the subpatterns
if resequencePatterns:
    for group in patternSequence.iter('group'):
        elementExists = False
        count = -1
        for patID in group.iter('patternID'):
            count += 1  # We keep track of the patID number so we can assign patterns in the same group to their respective new groups
            elementExists = True

            if count == 0:
                # Create the new groups
                newGroup_list = []
                for i in range(split_dict[patID.text]):
                    newGroup_list.append(etree.Element('group'))

            # Add the new patterns to the new groups 
            for i in range(split_dict[patID.text]):
                newPatternID = etree.SubElement(newGroup_list[i], 'patternID')
                if split_dict[patID.text] != 1:
                    newPatternID.text = patID.text + '_{}'.format(i)
                else:
                    newPatternID.text = patID.text

        
        # Now add the new groups to the new pattern sequence
        for i in range(split_dict[patID.text]):
            newPatternSequence.append(newGroup_list[i])

        if elementExists == False:
            newPatternSequence.append(copy.copy(group))


# Once we are finished we delete the old pattern list and add the new one
root.remove(patternList)
root.append(newPatternList)

root.remove(patternSequence)
root.append(newPatternSequence)


# Finally dump the new xml file
tree.write(outputFile)


