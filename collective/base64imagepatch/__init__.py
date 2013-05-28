# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from bs4 import BeautifulSoup
from zope.component import getMultiAdapter

import logging
import base64
import pkg_resources
import zope.interface
import zope.schema

try: 
    from zope.component.hooks import getSite
except:
    from zope.app.component.hooks import getSite

try:
    pkg_resources.get_distribution('Products.Archetypes')
except pkg_resources.DistributionNotFound:
    HAS_ARCHETYPES = False
else:
    HAS_ARCHETYPES = True
    from Products.Archetypes.interfaces.base import IBaseContent

try:
    pkg_resources.get_distribution('plone.dexterity')
except pkg_resources.DistributionNotFound:
    HAS_DEXTERITY = False
else:
    HAS_DEXTERITY = True
    from plone.dexterity.interfaces import IDexterityContent

logger = logging.getLogger('patch_base64images')

def initialize(context):
    """
    Initializer called when used as a Zope 2 product.
    """
    
def setuphandler():
    """

    """
    
'''    
def patch_base64_images_on_create(context, event):
    """ 
    Patch created content if it contains an inline images coded as base64 
    """
    patch_object(context)
'''
    
def patch_base64_images_on_modifiy(context, event):
    """ 
    Patch created content if it contains an inline images coded as base64 
    """
    patch_object(context)

    
def apply_patch_on_install():
    """ 
    Apply patch on all content object on package installation 
    """
    
    #get site_root
    portal = getSite()
    
    if HAS_ARCHETYPES:


        for obj in all_objects:
            patch_object(obj)
        
    if HAS_DEXTERITY:

        for obj in all_objects:
            patch_object(obj)
        
def patch_object(obj):
    
    logger.info( 
        "Patching Object \"" + 
        obj.title + 
        "\" on path: " + 
        obj.absolute_url() 
        )   
    
    container = obj.getParentNode()
    
    if container and container.isPrincipiaFolderish:
        logger.info( "Object Type is " + obj.portal_type)
        logger.info( "Object Parent is " + container.absolute_url() ) 
        
        if HAS_ARCHETYPES and IBaseContent.providedBy(obj):
            # Archetype Object
            for field in obj.schema.fields():
                if field.getType() == "Products.Archetypes.Field.TextField":
                    name = field.getName()
                    logger.info( 
                        "Object \""+obj.title+"\" is a Archetypes Type"+
                        " that has a field: \"" + field.getName() + 
                        "\" that is a Archetype TextField that could hold HTML" 
                        )
                    field_content = field.getRaw(obj)
                    if "base64" in field_content:
                        new_content = patch(container, obj, name, field_content)
                        field.getMutator(obj)(new_content)

        elif HAS_DEXTERITY and IDexterityContent.providedBy(obj):
            # Dexterity Object
            pt = obj.getTypeInfo()
            schema = pt.lookupSchema()
            for name in zope.schema.getFields(schema).keys():
                logger.info( "Object Field Name is " + name )
                logger.info( "Object Field Type is " + 
                    str( type( getattr(obj, name) ).__name__ ) ) 
                
                if type(getattr(obj, name)).__name__ == "RichTextValue":
                    logger.info( "object "+obj.title+" is a Dexterity Type" )  
                    field_content = getattr(obj, name).raw
                    if "base64" in field_content:
                        new_content = patch(container, obj, name, field_content)
                        
                        getattr(obj, name).__init__(raw=new_content)
        else:
            logger.info( "Unknown Content-Type-Framework for " + 
                obj.absolute_url() 
                )
    
def patch(container, obj, name, content):    
    """ Original Patch for both """
    counter = 0    
    logger.info( "Patching Object \"" + obj.title + 
        "\" on path: " + obj.absolute_url() + " field: " + name )
    soup = BeautifulSoup(content)
    all_images = soup.find_all('img')
    suffix_list = []
    suffix = obj.id + "." + name + ".image"
    for item in container.keys():
        
        if item.startswith(suffix):
            suffix_list.append(int(item[len(suffix):]))
            counter += 1
    suffix_list.sort()
    counter = max(suffix_list) + 1 if len(suffix_list) > 0 else 0

    for img_tag in all_images:
        if img_tag['src'].startswith('data'):
            image_params = img_tag['src'].split(';')
            mime_type = image_params[0][len("data:"):]
            img_data = image_params[1][len("base64,"):]
            img_id = suffix + str(counter)
            
            logger.info("Found image <img > with mime-type: " + mime_type)
                
            # create File in Container with base-name.image# 
            container.invokeFactory(
                "Image", 
                id=img_id, 
                mime_type=mime_type, 
                image=base64.b64decode(img_data))
            new_image = container[img_id]

            ## set src attribute to new src-location
            ## new_image.relative_url_path() includes Portal-Name
            ## id is correct, as it is directly in the same container as 
            ## the modified object
            img_tag['src'] = new_image.id 
            counter += 1
    
    if counter > 0:
        content = soup.find("body").contents[0].prettify()
        
    logger.info("New Content of Object "+obj.absolute_url()+":\n" + content)
    return content
    