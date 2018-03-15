import math, svgwrite, csv
from lxml import etree

def convert_coordinates(lat, lon):
    return lon*1000, lat*1000

file = 'map.osm'
bounds = {}
nodes = {}
ways = {}

for _, element in etree.iterparse(file, tag=['bounds', 'node', 'way']):
    if element.tag == 'bounds':
        bounds['minlat'] = element.get('minlat')
        bounds['minlon'] = element.get('minlon')
        bounds['maxlat'] = element.get('maxlat')
        bounds['maxlot'] = element.get('maxlon')
    elif element.tag == 'node':
        nodes[element.get('id')] = {'lat': element.get('lat'), 'lon': element.get('lon'), 'used': False, 'ways': []}
    elif element.tag == 'way':
        wayID = element.get('id')
        lst_nodesID = []
        for child in element.iter('nd', 'tag'):
            if child.tag == 'nd':
                childID = child.get('ref')
                lst_nodesID.append(childID)
            elif child.tag == 'tag' and child.get('k') == 'highway' and child.get('v') in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary',
            'unclassified', 'residential', 'road']:
                for nodeID in lst_nodesID:
                    if nodeID in nodes:
                        nodes[nodeID]['ways'].append(wayID)
                ways[wayID] = lst_nodesID

    element.clear()

adjList = {}

for wayID in ways:
    for nodeID in ways[wayID]:

        if nodeID not in nodes:
            continue
        if len(nodes[nodeID]['ways']) == 1:
            index = ways[wayID].index(nodeID)
            if index == 0:
                adjList[nodeID] = {ways[wayID][-1]}

            elif index == (len(ways[wayID]) - 1):
                adjList[nodeID] = {ways[wayID][0]}
        elif len(nodes[nodeID]['ways']) > 1:
            for wayID2 in nodes[nodeID]['ways']:
                if wayID2 != wayID:
                    index = ways[wayID2].index(nodeID)
                    for neighbour in ways[wayID2][index - 1::-1]:
                        if neighbour in nodes and len(nodes[neighbour]['ways']) > 1:
                            if nodeID not in adjList:
                                adjList[nodeID] = set()
                                adjList[nodeID].add(neighbour)
                            else:
                                adjList[nodeID].add(neighbour)
                            break
                        else:
                            continue

                    for neighbour in ways[wayID2][index + 1:]:
                        if neighbour in nodes and len(nodes[neighbour]['ways']) > 1:
                            if nodeID not in adjList:
                                adjList[nodeID] = set()
                                adjList[nodeID].add(neighbour)
                            else:
                                adjList[nodeID].add(neighbour)
                            break
                        else:
                            continue

with open('adjList.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['node', 'adj nodes'])
    for ID in adjList:
        writer.writerow([ID] + [[int(node) for node in adjList[ID]]])

svg_document = svgwrite.Drawing(filename='graph.svg')
for wayID in ways:
    printed_nodes = []
    for nodeID in ways[wayID]:
        if nodeID in nodes:
            nodes[nodeID]['used'] = True
            printed_nodes.append((convert_coordinates(float(nodes[nodeID]['lat']) - float(bounds['minlat']),
                                                     float(nodes[nodeID]['lon']) - float(bounds['minlon']))))
    svg_document.add(svgwrite.shapes.Polyline(printed_nodes, fill='none', stroke='brown', stroke_width=0.5))

svg_document.save()
fieldnames = list(adjList.keys())

with open('matrix.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[''] + fieldnames)

    writer.writeheader()
    for node in fieldnames:
        written_row = {neighbour: (1 if neighbour in adjList[node] else 0) for neighbour in fieldnames}
        written_row[''] = node
        writer.writerow(written_row)



