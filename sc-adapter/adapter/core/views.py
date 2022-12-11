from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import *

from django.shortcuts import render
from django.forms import model_to_dict

from sc_client import client
from .ostis import get_node_by_some_idtf, get_main_idtf_of_addr, get_entity_by_idtf, add_entity_to_kb,delete_entity_from_kb
from .models import entity
from sc_kpm import ScKeynodes

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



class EntityProvider(APIView):

    def get(self, request, node):
        # try: 
            keynodes = ScKeynodes()
            ent = get_entity_by_idtf(node, keynodes)
            print(f"{bcolors.WARNING}GET_GET_GET_GET_GET{bcolors.ENDC}")
            print ("ENTITY::::::::::::::::::")
            print(ent)
            JSON_ent = entity.obj_2_json(ent)
            print ("JSON::::::::::::::::::")
            print(JSON_ent)
            return Response(JSON_ent)
        # except Exception:
        #     return Response(status=HTTP_400_BAD_REQUEST)

    def post(self, request, node):
        # try: 
            keynodes = ScKeynodes()
            print(f"{bcolors.HEADER}POST_POST_POST_POST{bcolors.ENDC}")
            ent = entity.from_json(request)
            print(f"{bcolors.WARNING}GET_GET_GET_GET_GET{bcolors.ENDC}")
            print ("ENTITY::::::::::::::::::")
            print(ent)
            JSON_ent = entity.obj_2_json(ent)
            print ("JSON::::::::::::::::::")
            add_entity_to_kb(ent, keynodes)
            return Response(JSON_ent)
        # except Exception:
        #     return Response(status=HTTP_400_BAD_REQUEST)

    def delete(self, request, node):
            keynodes = ScKeynodes()
            ent = delete_entity_from_kb(node, keynodes)
            print(f"{bcolors.WARNING}GET_GET_GET_GET_GET{bcolors.ENDC}")
            print ("ENTITY::::::::::::::::::")
            print(ent)
            JSON_ent = entity.obj_2_json(ent)
            print ("JSON::::::::::::::::::")
            print(JSON_ent)
            return Response(JSON_ent)


class EntityKnower(APIView):

    def get(self, request, node):
        # try:
            keynodes = ScKeynodes()
            resolved_node = get_node_by_some_idtf(node, keynodes)
            if resolved_node == None :
                return Response(status=HTTP_204_NO_CONTENT)
            node_id = get_main_idtf_of_addr(resolved_node, keynodes)
            print (node_id)
            return Response({'response': node_id})
        # except Exception:
        #     return Response(status= HTTP_400_BAD_REQUEST)