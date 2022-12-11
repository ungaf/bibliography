from sc_client import client
from sc_client.models import *
from sc_client.constants import *

from sc_kpm import *
from sc_kpm.utils import *
from .models import entity, relation, Set
from langdetect import detect

def abstract_search_of_link_by_nrel(main_idtf, keynodes, nrel):
    print ("FROM OSTIS " + str(main_idtf))
    links = client.get_links_by_content(main_idtf)
    if len(links[0]) == 0 :
        return None
    node_addr_template = ScTemplate()
    node_addr_template.triple_with_relation(
        sc_types.UNKNOWN,
        sc_types.EDGE_D_COMMON_VAR,
        links[0][0],
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        keynodes[nrel])
    node_addr = client.template_search(node_addr_template)
    if len(node_addr) < 1:
        return None
    return node_addr[0].get(0)

def get_node_by_main_idtf(main_idtf, keynodes):
    return abstract_search_of_link_by_nrel(main_idtf, keynodes, "nrel_main_idtf")

def get_node_by_idtf(main_idtf, keynodes):
    return abstract_search_of_link_by_nrel(main_idtf, keynodes, "nrel_idtf")

def get_main_idtf_of_addr(node_addr, keynodes):
    print("BEFORE MAIN IDTF: " + get_system_idtf(node_addr))
    main_idtf_template = ScTemplate()
    main_idtf_template.triple_with_relation(
        node_addr,
        sc_types.EDGE_D_COMMON_VAR,
        "_link",
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        keynodes["nrel_main_idtf"])
    main_rrel = client.template_search(main_idtf_template)

    for item in main_rrel:
        return client.get_link_content(item.get(2))[0].data

def get_node_by_some_idtf(node:str, keynodes) -> ScAddr:
    print ("MAIN IDTF")
    resolved_node = get_node_by_main_idtf(node, keynodes)
    if resolved_node == None :
        print ("JUST IDTF")
        resolved_node = get_node_by_idtf(node, keynodes)
    if resolved_node == None :
        print ("JUST GET")
        resolved_node = keynodes.get(node)
    if not resolved_node.is_valid() :
        return None
    return resolved_node

def get_node_by_some_idtf_or_create(node:str, keynodes:ScKeynodes) -> ScAddr:
    node_scaddr = get_node_by_some_idtf(node, keynodes)
    if node_scaddr == None:
        return keynodes.resolve(node, sc_types.NODE_CONST_CLASS)
    return node_scaddr

def get_nrel_relations(src_node, trg_node):
    all_related_template = ScTemplate()
    all_related_template.triple_with_relation(
        src_node,
        sc_types.EDGE_D_COMMON_VAR,
        trg_node,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        sc_types.NODE_VAR_NOROLE)
    return client.template_search(all_related_template)

def abstract_search_of_3iterator(src, trg, keynodes):
    all_is = ScTemplate()
    all_is.triple(
        src,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        trg)
    result = client.template_search(all_is)
    set = []
    for item in result:
        idtf =  get_main_idtf_of_addr(item.get(0),keynodes)
        if idtf is not None:
            set.append(idtf)
    return set

def get_all_child_sets(node_addr, keynodes):
    return abstract_search_of_3iterator(node_addr, "_trg", keynodes)

def get_all_parent_sets(node_addr, keynodes):
    return abstract_search_of_3iterator("_src", node_addr, keynodes)

def get_all_sets(node_addr, keynodes) :
    return Set(
        parent= get_all_parent_sets(node_addr, keynodes),
        child=get_all_child_sets(node_addr, keynodes)
    )

def get_all_nrel_relations(node_addr, keynodes):
    all_related = get_nrel_relations(src_node= node_addr, trg_node= sc_types.NODE_VAR)
    all_related.extend(get_nrel_relations(src_node= sc_types.NODE_VAR, trg_node= node_addr))
    relations = []
    for item in all_related:
        src_addr = item.get(0)
        trg_addr = item.get(2)
        rrel_arg = item.get(3)
        src = get_main_idtf_of_addr(src_addr, keynodes)
        trg = get_main_idtf_of_addr(trg_addr, keynodes)
        rrel = get_main_idtf_of_addr(rrel_arg, keynodes)
        if (src is None):
            src = get_all_child_sets(src_addr, keynodes)
        if (trg is None):
            trg = get_all_child_sets(trg_addr, keynodes)
        relations.append(
            relation(src, 
                     trg, 
                     rrel))
    return relations 

def get_some_idtf(node: ScAddr, keynodes):
    resolved_node = get_main_idtf_of_addr(node, keynodes)
    if resolved_node == None :
        return get_system_idtf(node)
    else :
        return resolved_node

def get_entity_by_idtf(node:str, keynodes:ScKeynodes) :
    node_addr = get_node_by_some_idtf(node, keynodes)
    if node_addr == None :
        return None
    all_rrels = get_all_nrel_relations(node_addr, keynodes)
    concept_belongs = get_all_sets(node_addr, keynodes)
    return entity (
        main_idtf=get_some_idtf(node_addr, keynodes),
        system_idtf=get_system_idtf(node_addr),
        relations=all_rrels,
        sets=concept_belongs
    )

def add_main_id_to_node(main_idtf:str, node:ScAddr, keynodes:ScKeynodes):
    lang = detect(main_idtf)
    main_idtf_link = create_link(main_idtf,ScLinkContentType.STRING, sc_types.LINK_CONST)
    edge = create_edge(sc_types.EDGE_D_COMMON_CONST,node, main_idtf_link)
    create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, keynodes["nrel_main_idtf"], edge) 
    create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,keynodes["lang_"+ lang], main_idtf_link)

def relation_to_system_view(rel_name:str):
    rel_name = rel_name.strip()
    if rel_name.find("*") == -1:
        rel_name = rel_name + "*"
    return " " + rel_name + " "

def create_node_with_multiple_nodes(nodes:list, keynodes:ScKeynodes) :
    empty_node = create_node(sc_types.NODE_CONST_CLASS)
    for node in nodes:
        create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,empty_node, get_node_by_some_idtf_or_create(node, keynodes))
    return empty_node

def get_relation_node_from_idtf_or_list(node, keynodes:ScKeynodes):
    if isinstance(node, list) :
        return create_node_with_multiple_nodes(node, keynodes)
    else:
        return get_node_by_some_idtf_or_create(node, keynodes)

def add_relations_to_node(relations:list, keynodes:ScKeynodes):
    for relation in  relations:
        src_name = relation.src
        trg_name = relation.trg
        sys_relation_name = relation_to_system_view(relation.name)
        relation = get_node_by_some_idtf_or_create(sys_relation_name, keynodes)
        src = get_relation_node_from_idtf_or_list(src_name, keynodes)
        trg = get_relation_node_from_idtf_or_list(trg_name, keynodes)
        edge = create_edge(sc_types.EDGE_D_COMMON_CONST,src, trg)
        create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, relation, edge)

def add_sets_to_node(sets:Set, node:ScAddr, keynodes:ScKeynodes):
    for p_node in sets.parent:
        p_node_sc_sddr = get_node_by_some_idtf_or_create(p_node, keynodes)
        create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,p_node_sc_sddr, node)
    for c_node in sets.child:
        c_node_sc_sddr = get_node_by_some_idtf_or_create(c_node, keynodes)
        create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,node, c_node_sc_sddr)

def add_entity_to_kb(entity:entity, keynodes:ScKeynodes) :
    entity_node = get_node_by_main_idtf(entity.main_idtf, keynodes)
    if entity_node == None :
        entity_node = keynodes.resolve(entity.system_idtf, sc_types.NODE_CONST_CLASS)
        add_main_id_to_node(entity.main_idtf, entity_node , keynodes)

    add_relations_to_node(entity.relations, keynodes)
    add_sets_to_node(entity.sets, entity_node, keynodes)

def delete_entity_from_kb(node:str, keynodes:ScKeynodes) :
    ent = get_entity_by_idtf(node, keynodes)
    addr = get_node_by_some_idtf(ent.main_idtf, keynodes)

    main_idtf_links = client.get_links_by_content(ent.main_idtf)[0]
    for link in main_idtf_links:
        print (client.get_link_content(link))
        client.delete_elements(link)
    print ("======================================SYSTEM============================")
    system_idtf_links = client.get_links_by_content(ent.system_idtf)[0]
    for link in system_idtf_links:
        print (client.get_link_content(link))
        client.delete_elements(link)
    
    if client.delete_elements(addr):
        return ent
    else:
        return None