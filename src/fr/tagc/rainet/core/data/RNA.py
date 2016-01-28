
from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from fr.tagc.rainet.core.util.sql.Base import Base
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager

from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.log.Logger import Logger

from fr.tagc.rainet.core.data import DataConstants
from fr.tagc.rainet.core.data.Gene import Gene

from fr.tagc.rainet.core.util.exception.NotRequiredInstantiationException import NotRequiredInstantiationException
from sqlalchemy.orm.base import instance_dict



# #
# This class describes a RNA models obtained from querying Ensembl BioMart
#
class RNA( Base ):
    __tablename__ = 'RNA'

    # The Ensembl Transcript ID
    transcriptID = Column( String, primary_key = True )
#     # The parent gene Ensembl Gene ID
    geneID = Column ( String, ForeignKey("Gene.geneID") )
    # The Ensembl Peptide ID, if existing
    peptideID = Column( String )
    # The type/category of the transcript
    transcriptBiotype = Column( String )
    # The length of the transcript
    transcriptLength = Column( Integer )
    # The annotation source of the transcript
    transcriptSource = Column( String )
    # The confidence status of the transcript
    transcriptStatus = Column( String )
    # The Ensembl confidence level of the transcript
    transcriptTsl = Column ( String )
    # Presence or absence of this transcript on GENCODE Basic dataset
    transcriptGencodeBasic = Column ( Boolean )
    # The genomic start position coordinate of transcript
    transcriptStart = Column( Integer )
    # The genomic end position coordinate of transcript
    transcriptEnd = Column( Integer )
    # The genomic strandness of transcript
    transcriptStrand = Column ( Integer )
    # The chromosome name of transcript
    chromosomeName = Column ( String )
    # The percentage of GC content in transcript
    percentageGCContent = Column ( Float )
    # The list of RNA cross references
    crossReferences = relationship( 'RNACrossReference', backref = 'RNA' )
 

    # #
    # The RNA constructor
    # 
    # @param 
    #### dr: NEED TO FILL documentation    
    # also adding Gene table...
    def __init__( self, transcript_ID, gene_ID, peptide_ID, transcript_biotype, transcript_length, transcript_source, transcript_status, transcript_tsl, transcript_gencode_basic, transcript_start, transcript_end, transcript_strand, chromosome_name, percentage_GC_content):
        
        #=======================================================================
        # Fill the main protein variables
        #=======================================================================

        if transcript_ID != "":
            self.transcriptID = transcript_ID
        else:
            raise RainetException( "RNA.__init__ : The value of transcript ID is empty: " + str( transcript_ID ) )   
        
        self.peptideID = peptide_ID

        if transcript_biotype != "":
            self.transcriptBiotype = transcript_biotype
        else:
            raise RainetException( "RNA.__init__ : The value of transcript biotype is empty: " + str( transcript_gencode_basic ) )   
        
        try:
            self.transcriptLength = int( transcript_length )
        except ValueError as ve:
            raise RainetException( "RNA.__init__ : The value of transcript length is not an integer: " + str( transcript_length ), ve )
        
        self.transcriptSource = transcript_source
        
        self.transcriptStatus = transcript_status
        
        self.transcriptTsl = transcript_tsl
        
        if transcript_gencode_basic == "GENCODE basic":
            self.transcriptGencodeBasic = 1
        elif transcript_gencode_basic == "":
            self.transcriptGencodeBasic = 0
        else:
            raise RainetException( "RNA.__init__ : The value of GENCODE basic is not identified: " + str( transcript_gencode_basic ))   
                 
        try:
            self.transcriptStart = int( transcript_start )
        except ValueError as ve:
            raise RainetException( "RNA.__init__ : The value of transcript start is not an integer: " + str( transcript_start ), ve )
        
        try:
            self.transcriptEnd = int( transcript_end )
        except ValueError as ve:
            raise RainetException( "RNA.__init__ : The value of transcript end is not an integer: " + str( transcript_end ), ve )
        
        try:
            self.transcriptStrand = int( transcript_strand )
        except ValueError as ve:
            raise RainetException( "RNA.__init__ : The value of transcript strand is not an integer: " + str( transcript_strand ), ve )
        
        self.chromosomeName = chromosome_name
        
        self.percentageGCContent = percentage_GC_content
        
        try:
            self.percentageGCContent = float ( percentage_GC_content )
        except ValueError as ve:
            raise RainetException( "RNA.__init__ : The value of GC content percentage end is not a float: " + str( percentage_GC_content ), ve )

        
        #=======================================================================
        # Build the Gene objects related to the RNA
        #=======================================================================

        # each Gene can contain several transcripts. get instance of gene and see if already present, if not, create new Gene entry

        sql_session = SQLManager.get_instance().get_session()
        gene = sql_session.query( Gene ).filter( Gene.geneID == gene_ID).first()

        #sql_session.query( RNA).filter( RNA.geneID == Gene.geneID, Gene.geneID == gene_name).all() #if wanting to query all transcripts of a specific Gene
 
        if gene == None: #if no Gene with that Gene ID found, create one
            gene = Gene( gene_ID )
 
        gene.add_rna( self )
        
        sql_session.add( gene )

        # Add the current RNA to database
        self.add_to_session()

    # #
    # Add a RNACrossReference to the RNA cross reference list
    #
    # @param cross_reference : string - A RNACrossReference instance
    def add_cross_reference( self, cross_reference ):
        
        if cross_reference != None:
            self.crossReferences.append( cross_reference )

    # #
    # Add the object to SQLAlchemy session
    def add_to_session( self ):
    
        sql_session = SQLManager.get_instance().get_session()
        sql_session.add( self )

