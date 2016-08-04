
from sqlalchemy import Column, String, ForeignKey
from fr.tagc.rainet.core.util.sql.Base import Base
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager

from fr.tagc.rainet.core.util.exception.NotRequiredInstantiationException import NotRequiredInstantiationException
from fr.tagc.rainet.core.util.exception.RainetException import RainetException

from fr.tagc.rainet.core.data.ProteinCrossReference import ProteinCrossReference
from fr.tagc.rainet.core.data.Protein import Protein
from fr.tagc.rainet.core.data.SynonymGeneSymbol import SynonymGeneSymbol

# #
# This class describes a annotation of protein on Bioplex clusters
#
class ProteinBioplexAnnotation( Base ):
    __tablename__ = 'ProteinBioplexAnnotation'
    
    # The Bioplex cluster annotation
    bioplex_cluster_id = Column( String, ForeignKey( 'BioplexCluster.bioplexID', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    # The annotated protein
    protein_id = Column( String, ForeignKey( 'Protein.uniprotAC', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)  
    
    #
    # The constructor of the class
    #
    # @param bioplex_cluster_id : string - The ID of the Bioplex cluster associated to the protein
    def __init__(self, bioplex_cluster_id, protein_id):
                
        sql_session = SQLManager.get_instance().get_session()
         
        #=======================================================================
        # Search for the Bioplex cluster corresponding to the given Bioplex cluster ID
        #=======================================================================
        # -- make the query
        from fr.tagc.rainet.core.data.BioplexCluster import BioplexCluster
        clusters_list = sql_session.query( BioplexCluster).filter( BioplexCluster.bioplexID == bioplex_cluster_id).all()
         
        # --Check if a single cross reference is found. If not, raise an issue
        cluster_id = None
        if clusters_list != None and len( clusters_list) > 0:
            if len( clusters_list) == 1:
                cluster_id = clusters_list[0]
            else:
                raise RainetException( "ProteinBioplexAnnotation.init : Abnormal number of Bioplex clusters found for cluster_id = " + cluster_id + " : " + str( len( clusters_list))) 
        else:
            raise NotRequiredInstantiationException( "ProteinBioplexAnnotation.init : No Bioplex cluster found for cluster id = " + cluster_id)
 
        if cluster_id == None:
            raise RainetException( "ProteinBioplexAnnotation.init : returned cross reference is None for " + cluster_id)
         
        #=======================================================================
        # Get the ProteinCrossReference corresponding to the provided Biocomplex protein ID
        # (cross_reference) in order to convert it to Uniprot AC
        #=======================================================================
        # -- make the query
        protein_crossref_list = sql_session.query( SynonymGeneSymbol.protein_id).filter( SynonymGeneSymbol.uniprotGeneSymbol_id == protein_id).all()
         
        # --Check if a single cross reference is found. If not, raise an issue
        if protein_crossref_list == None or len( protein_crossref_list) == 0:
            raise NotRequiredInstantiationException( "ProteinBioplexAnnotation.init : No ProteinCrossReference found for cross reference = " + protein_id)

        #=======================================================================
        # Search from the Proteins corresponding to the cross references found
        # in the previous step. Then build the association between the Protein
        # and the BioplexCluster 
        #=======================================================================
        for cross_ref in protein_crossref_list:
            # -- make the query
            protein_list = sql_session.query( Protein).filter( Protein.uniprotAC == cross_ref.protein_id).all()
             
            # --Check if a single Protein is found. If not, raise an issue
            protein = None
            if protein_list != None and len( protein_list) > 0:
                if len( protein_list) == 1:
                    protein = protein_list[0]
                else:
                    raise RainetException( "ProteinBioplexAnnotation.init : Abnormal number of Protein found for cross reference = " + cross_ref.protein_id + " : " + str( len( protein_list))) 
            else:
                raise NotRequiredInstantiationException( "ProteinBioplexAnnotation.init : No Protein found for uniprotAC = " + cross_ref.protein_id)
     
            # -- Check if the Protein found is not None
            if protein == None:
                raise RainetException( "ProteinBioplexAnnotation.init : returned Protein is None for UniprotAC" + cross_ref.protein_id)
                 
            # -- Build the relation between the Bioplex cluster and the Protein
            cluster_id.add_annotated_protein( protein)
            sql_session.add( cluster_id)
            sql_session.add( protein)
            
        # Raise the Exception to indicate the instance must not be inserted since it is automatically created 
        raise NotRequiredInstantiationException( "ProteinBioplexAnnotation.init : ProteinBioplexAnnotation objects do not have to be inserted by __init__ since they are created by BioplexCluster to Protein association table.")
        
            
    ##
    # Add the object to SQLAlchemy session if it is linked to a protein
    def add_to_session(self):
    
        sql_session = SQLManager.get_instance().get_session()
        sql_session.add( self)
    