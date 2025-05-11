# app/services/scene_segment_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
import traceback

from app.models.scene_segments import SceneSegment, SceneSegmentComponent, ComponentType
from app.models.script import Script
from app.models.beats import Beat
from app.models.scenes import SceneDescription
from app.schemas.scene_segment import SceneSegmentCreate, SceneSegmentUpdate, ComponentCreate, ComponentUpdate

logger = logging.getLogger(__name__)


class SceneSegmentService:
    @staticmethod
    def get_next_component_position(
        db: Session,
        segment_id: UUID
    ) -> float:
        """
        Get the next available position for a component within a segment.
        
        This calculates the appropriate position value for adding a new component
        to the end of a segment.
        """
        
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        if not segment:
            raise

        # Query for the highest component position in this segment
        result = db.query(func.max(SceneSegmentComponent.position)).filter(
            and_(
                SceneSegmentComponent.scene_segment_id == segment_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).scalar()
        
        # If no components exist, start at 1000
        if result is None:
            return 1000.0
        
        # Otherwise, add 1000 to the highest position
        return result + 1000.0


    @staticmethod
    def fetch_next_segment_number(db: Session, script_id: str):
        result = db.query(func.max(SceneSegment.segment_number)).filter(
            and_(
                SceneSegment.script_id == script_id,
                SceneSegment.is_deleted.is_(False)
            )
        ).scalar()
        return result

    @staticmethod
    def create_scene_segment(db: Session, scene_segment: SceneSegmentCreate) -> SceneSegment:
        """
        Create a new scene segment with its components
        """
        # Verify script exists
        script = db.query(Script).filter(Script.id == scene_segment.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
            
        # Verify beat if provided
        if scene_segment.beat_id:
            beat = db.query(Beat).filter(
                and_(
                    Beat.id == scene_segment.beat_id,
                    Beat.script_id == scene_segment.script_id
                )
            ).first()
            if not beat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Beat not found or does not belong to this script"
                )
                
        # Verify scene description if provided
        if scene_segment.scene_description_id:
            scene_desc = db.query(SceneDescription).filter(
                SceneDescription.id == scene_segment.scene_description_id
            ).first()
            if not scene_desc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scene description not found"
                )
                
            # If both beat and scene description are provided, verify they're related
            if scene_segment.beat_id and scene_desc.beat_id != scene_segment.beat_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scene description does not belong to the specified beat"
                )
        
        # Create the scene segment
        db_scene_segment = SceneSegment(
            script_id=scene_segment.script_id,
            beat_id=scene_segment.beat_id,
            scene_description_id=scene_segment.scene_description_id,
            segment_number=scene_segment.segment_number
        )
        
        # Add to session and flush to get ID before creating components
        db.add(db_scene_segment)
        db.flush()
        
        # Create components
        for component_data in scene_segment.components:
            component = SceneSegmentComponent(
                scene_segment_id=db_scene_segment.id,
                component_type=component_data.component_type,
                position=component_data.position,
                content=component_data.content,
                character_name=component_data.character_name,
                parenthetical=component_data.parenthetical
            )
            db.add(component)
        
        try:
            db.commit()
            db.refresh(db_scene_segment)
            return db_scene_segment
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating scene segment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating scene segment: {str(e)}"
            )

    @staticmethod
    def get_scene_segments_for_script(
        db: Session, 
        script_id: UUID,
        skip: int = 0,
        limit: int = 100,
        beat_id: Optional[UUID] = None,
        scene_description_id: Optional[UUID] = None
    ) -> Tuple[List[SceneSegment], int]:
        """
        Get scene segments for a script with optional filtering
        """
        query = db.query(SceneSegment).filter(
            and_(
                SceneSegment.script_id == script_id,
                SceneSegment.is_deleted.is_(False)
            )
        )
        
        # Apply optional filters
        if beat_id:
            query = query.filter(SceneSegment.beat_id == beat_id)
        if scene_description_id:
            query = query.filter(SceneSegment.scene_description_id == scene_description_id)
            
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        segments = query.order_by(SceneSegment.segment_number).offset(skip).limit(limit).all()
        
        for segment in segments:
            segment.components = [comp for comp in segment.components if not comp.is_deleted]

        
        return segments, total

    @staticmethod
    def get_scene_segment(db: Session, segment_id: UUID) -> SceneSegment:
        """
        Get a specific scene segment by ID
        """
        segment = db.query(SceneSegment).filter(
            and_(
                SceneSegment.id == segment_id,
                SceneSegment.is_deleted.is_(False)
            )
        ).first()
        
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene segment not found"
            )
            
        return segment

    @staticmethod
    def update_scene_segment(
        db: Session, 
        segment_id: UUID, 
        update_data: SceneSegmentUpdate
    ) -> SceneSegment:
        """
        Update a scene segment's metadata
        """
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        
        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Verify beat if changing
        if 'beat_id' in update_dict and update_dict['beat_id']:
            beat = db.query(Beat).filter(
                and_(
                    Beat.id == update_dict['beat_id'],
                    Beat.script_id == segment.script_id
                )
            ).first()
            if not beat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Beat not found or does not belong to this script"
                )
                
        # Verify scene description if changing
        if 'scene_description_id' in update_dict and update_dict['scene_description_id']:
            scene_desc = db.query(SceneDescription).filter(
                SceneDescription.id == update_dict['scene_description_id']
            ).first()
            if not scene_desc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scene description not found"
                )
                
            new_beat_id = update_dict.get('beat_id', segment.beat_id)
            if new_beat_id and scene_desc.beat_id != new_beat_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scene description does not belong to the specified beat"
                )
        
        # Update the segment
        for key, value in update_dict.items():
            setattr(segment, key, value)
            
        try:
            db.commit()
            db.refresh(segment)
            return segment
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating scene segment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating scene segment: {str(e)}"
            )

    @staticmethod
    def delete_scene_segment(db: Session, segment_id: UUID) -> bool:
        """
        Soft delete a scene segment
        """
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        
        segment.soft_delete()
        # Note: Components are soft deleted through the soft_delete method
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting scene segment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting scene segment: {str(e)}"
            )

    @staticmethod
    def reorder_scene_segment(
        db: Session, 
        segment_id: UUID, 
        new_segment_number: float
    ) -> SceneSegment:
        """
        Reorder a scene segment within its script
        """
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        
        # Update segment number
        segment.segment_number = new_segment_number
        
        try:
            db.commit()
            db.refresh(segment)
            return segment
        except Exception as e:
            db.rollback()
            logger.error(f"Error reordering scene segment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reordering scene segment: {str(e)}"
            )

    # Component methods
    @staticmethod
    def add_component(
        db: Session, 
        segment_id: UUID, 
        component: ComponentCreate
    ) -> SceneSegmentComponent:
        """
        Add a new component to a scene segment
        """
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        
        # Create the component
        db_component = SceneSegmentComponent(
            scene_segment_id=segment.id,
            component_type=component.component_type,
            position=component.position,
            content=component.content,
            character_name=component.character_name,
            parenthetical=component.parenthetical
        )
        
        db.add(db_component)
        
        try:
            db.commit()
            db.refresh(db_component)
            return db_component
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding component: {str(e)}"
            )

    @staticmethod
    def update_component(
        db: Session, 
        component_id: UUID, 
        update_data: ComponentUpdate
    ) -> SceneSegmentComponent:
        """
        Update a component
        """
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
            
        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(component, key, value)
            
        try:
            db.commit()
            db.refresh(component)
            return component
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating component: {str(e)}"
            )

    @staticmethod
    def delete_component(db: Session, component_id: UUID) -> bool:
        """
        Soft delete a component
        """
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
            
        component.soft_delete()
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting component: {str(e)}"
            )

    @staticmethod
    def reorder_component(
        db: Session, 
        component_id: UUID, 
        new_position: float
    ) -> SceneSegmentComponent:
        """
        Reorder a component within its segment
        """
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
            
        # Update position
        component.position = new_position
        
        try:
            db.commit()
            db.refresh(component)
            return component
        except Exception as e:
            db.rollback()
            logger.error(f"Error reordering component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reordering component: {str(e)}"
            )
            
    @staticmethod
    def create_segment_with_components_from_text(
        db: Session,
        script_id: UUID,
        segment_number: float,
        text: str,
        beat_id: Optional[UUID] = None,
        scene_description_id: Optional[UUID] = None
    ) -> SceneSegment:
        """
        Intelligently create a scene segment from raw text, detecting component types.
        
        This method parses plain text and creates appropriate components based on 
        screenplay formatting conventions.
        """
        # Create empty segment first
        segment = SceneSegment(
            script_id=script_id,
            beat_id=beat_id,
            scene_description_id=scene_description_id,
            segment_number=segment_number
        )
        db.add(segment)
        db.flush()  # Get the ID without committing
        
        # Split text into lines
        lines = text.splitlines()
        
        # Variables to track parsing state
        current_position = 1000.0
        components = []
        
        # Scene headings are typically ALL CAPS or at least capitalized and begin the segment
        if lines and (lines[0].isupper() or lines[0].istitle()):
            # Create heading component
            heading = SceneSegmentComponent(
                scene_segment_id=segment.id,
                component_type=ComponentType.HEADING,
                position=current_position,
                content=lines[0].strip()
            )
            components.append(heading)
            current_position += 1000.0
            lines = lines[1:]  # Remove processed line
        
        # Process remaining lines
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Try to detect component type
            if line.isupper() and ":" not in line:  # Possible character name
                # Look ahead for dialogue
                dialogue_content = []
                j = i + 1
                while j < len(lines) and lines[j].strip() and not lines[j].strip().isupper():
                    dialogue_content.append(lines[j].strip())
                    j += 1
                
                # Check for parenthetical
                parenthetical = None
                if dialogue_content and dialogue_content[0].startswith('(') and dialogue_content[0].endswith(')'):
                    parenthetical = dialogue_content[0][1:-1]  # Remove parentheses
                    dialogue_content = dialogue_content[1:]  # Remove parenthetical from dialogue
                
                # Create dialogue component
                if dialogue_content:
                    dialogue = SceneSegmentComponent(
                        scene_segment_id=segment.id,
                        component_type=ComponentType.DIALOGUE,
                        position=current_position,
                        content="\n".join(dialogue_content),
                        character_name=line,
                        parenthetical=parenthetical
                    )
                    components.append(dialogue)
                    current_position += 1000.0
                    i = j  # Skip processed lines
                    continue
            
            # Check for transition (ends with TO:)
            if line.endswith("TO:") and line.isupper():
                transition = SceneSegmentComponent(
                    scene_segment_id=segment.id,
                    component_type=ComponentType.TRANSITION,
                    position=current_position,
                    content=line
                )
                components.append(transition)
                current_position += 1000.0
                i += 1
                continue
            
            # Default to action
            # Collect consecutive action lines
            action_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not (
                lines[j].strip().isupper() or 
                lines[j].strip().endswith("TO:") or
                lines[j].strip().startswith('(')
            ):
                action_lines.append(lines[j].strip())
                j += 1
            
            action = SceneSegmentComponent(
                scene_segment_id=segment.id,
                component_type=ComponentType.ACTION,
                position=current_position,
                content="\n".join(action_lines)
            )
            components.append(action)
            current_position += 1000.0
            i = j
        
        # Add components to DB
        db.add_all(components)
        
        try:
            db.commit()
            db.refresh(segment)
            return segment
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating segment from text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating segment from text: {str(e)}"
            )
            
    @staticmethod
    def batch_update_components(
        db: Session,
        segment_id: UUID,
        components_data: List[Dict[str, Any]]
    ) -> List[SceneSegmentComponent]:
        """
        Efficiently update multiple components at once.
        
        This method handles the common auto-save scenario by:
        1. Adding new components
        2. Updating existing components
        3. Handling component reordering
        """
        segment = SceneSegmentService.get_scene_segment(db, segment_id)
        result = []
        
        # Get existing components (not deleted)
        existing_components = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.scene_segment_id == segment_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).all()
        
        # Create lookup map for existing components
        existing_by_id = {comp.id: comp for comp in existing_components}
        
        # Process each component update
        for component_data in components_data:
            component_id = component_data.get('id')
            
            if component_id and component_id in existing_by_id:
                # Update existing component
                component = existing_by_id[component_id]
                
                # Apply updates
                for key, value in component_data.items():
                    if key != 'id' and key != 'scene_segment_id':
                        setattr(component, key, value)
                
                result.append(component)
            else:
                # Create new component
                new_component = SceneSegmentComponent(
                    scene_segment_id=segment_id,
                    component_type=component_data['component_type'],
                    position=component_data['position'],
                    content=component_data['content'],
                    character_name=component_data.get('character_name'),
                    parenthetical=component_data.get('parenthetical')
                )
                db.add(new_component)
                result.append(new_component)
        
        try:
            db.commit()
            # Refresh all components to get updated data
            for component in result:
                db.refresh(component)
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Error batch updating components: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error batch updating components: {str(e)}"
            )
            
    @staticmethod
    def export_screenplay_text(
        db: Session,
        script_id: UUID
    ) -> str:
        """
        Export the screenplay as formatted text.
        
        Returns the screenplay in standard screenplay format as plain text.
        """
        # Get all scene segments in order
        segments = db.query(SceneSegment).filter(
            and_(
                SceneSegment.script_id == script_id,
                SceneSegment.is_deleted.is_(False)
            )
        ).order_by(SceneSegment.segment_number).all()
        
        if not segments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scene segments found for this script"
            )
            
        formatted_text = []
        
        for segment in segments:
            # Get all components for this segment
            components = db.query(SceneSegmentComponent).filter(
                and_(
                    SceneSegmentComponent.scene_segment_id == segment.id,
                    SceneSegmentComponent.is_deleted.is_(False)
                )
            ).order_by(SceneSegmentComponent.position).all()
            
            for component in components:
                if component.component_type == ComponentType.HEADING:
                    # Scene headings are capitalized
                    formatted_text.append(component.content.upper())
                    formatted_text.append("")  # Add blank line
                
                elif component.component_type == ComponentType.ACTION:
                    # Action descriptions are block formatted
                    formatted_text.append(component.content)
                    formatted_text.append("")  # Add blank line
                
                elif component.component_type == ComponentType.DIALOGUE:
                    # Character name is centered and capitalized
                    formatted_text.append(component.character_name.upper())
                    
                    # Add parenthetical if present
                    if component.parenthetical:
                        formatted_text.append(f"({component.parenthetical})")
                    
                    # Dialogue is indented
                    formatted_text.append(component.content)
                    formatted_text.append("")  # Add blank line
                
                elif component.component_type == ComponentType.TRANSITION:
                    # Transitions are right-aligned and capitalized
                    formatted_text.append(component.content.upper())
                    formatted_text.append("")  # Add blank line
        
        return "\n".join(formatted_text)
        
    @staticmethod
    def auto_format_component(
        db: Session,
        component_id: UUID
    ) -> SceneSegmentComponent:
        """
        Automatically apply formatting corrections to a component.
        
        This is useful for ensuring screenplay formatting standards are maintained.
        """
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
            
        # Apply formatting based on component type
        if component.component_type == ComponentType.HEADING:
            # Scene headings should be uppercase with standard formatting
            heading = component.content.upper()
            
            # Ensure it starts with INT. or EXT. if not already
            if not (heading.startswith("INT.") or heading.startswith("EXT.") or 
                    heading.startswith("INT./EXT.") or heading.startswith("EXT./INT.")):
                if "INT." in heading:
                    heading = "INT. " + heading.replace("INT.", "")
                elif "EXT." in heading:
                    heading = "EXT. " + heading.replace("EXT.", "")
                else:
                    # Default to INT. if no location indicator
                    heading = "INT. " + heading
            
            # Ensure there's a time of day
            if not any(time in heading for time in ["DAY", "NIGHT", "MORNING", "EVENING", "AFTERNOON", "DAWN", "DUSK", "LATER", "CONTINUOUS", "SAME TIME"]):
                heading += " - DAY"
                
            component.content = heading
            
        elif component.component_type == ComponentType.DIALOGUE:
            # Character names should be uppercase
            if component.character_name:
                component.character_name = component.character_name.upper()
                
            # Parentheticals should be lowercase and in parentheses
            if component.parenthetical:
                # Remove existing parentheses if present
                parenthetical = component.parenthetical.strip("()")
                # Convert to lowercase and add parentheses
                component.parenthetical = parenthetical.lower()
                
        elif component.component_type == ComponentType.TRANSITION:
            # Transitions should be uppercase and end with TO:
            transition = component.content.upper()
            if not transition.endswith("TO:"):
                transition += " TO:"
            component.content = transition
            
        try:
            db.commit()
            db.refresh(component)
            return component
        except Exception as e:
            db.rollback()
            logger.error(f"Error formatting component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error formatting component: {str(e)}"
            )
        

    @staticmethod
    def apply_script_changes(
        db: Session,
        script_id: UUID,
        changed_segments: Dict[str, List[Dict[str, Any]]],
        deleted_elements: List[str],
        deleted_segments: List[str],
        new_segments: Optional[List[Dict[str, Any]]] = None,
        new_components_in_existing_segments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Apply multiple changes to script segments and components in a single transaction.
        
        Tracks and returns mappings from frontend temporary IDs to backend-generated UUIDs.
        
        Args:
            db: Database session
            script_id: ID of the script being modified
            changed_segments: Dictionary of segment_id -> list of modified components
            deleted_elements: List of component IDs to delete
            deleted_segments: List of segment IDs to delete
            new_segments: List of new segments with their components
            new_components_in_existing_segments: List of new components to add to existing segments
            
        Returns:
            Dictionary with success status, counts of changes, and ID mappings
        """
        try:
            # Verify script exists
            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Script not found"
                )
            
            # Initialize tracking counts
            updated_count = 0
            deleted_component_count = 0
            deleted_segment_count = 0
            created_segment_count = 0
            created_component_count = 0
            
            # Initialize ID mapping dictionaries
            segment_id_map = {}  # Maps frontend IDs to backend UUIDs for segments
            component_id_map = {}  # Maps frontend IDs to backend UUIDs for components
            
            # 1. Process new segments (if any)
            if new_segments:
                logger.info(f"Processing {len(new_segments)} new segments")
                for segment_data in new_segments:
                    try:
                        segment_data = segment_data.model_dump()
                        # Create the scene segment
                        segment_number = segment_data.get('segmentNumber')
                        
                        # Get the frontend ID for mapping
                        frontend_segment_id = segment_data.get('frontendId')
                        
                        # Convert beat_id and scene_description_id to UUID if they're strings
                        beat_id_str = segment_data.get('beatId')
                        scene_description_id_str = segment_data.get('sceneDescriptionId')
                        
                        beat_id = UUID(beat_id_str) if beat_id_str and isinstance(beat_id_str, str) else beat_id_str
                        scene_description_id = UUID(scene_description_id_str) if scene_description_id_str and isinstance(scene_description_id_str, str) else scene_description_id_str
                        
                        db_segment = SceneSegment(
                            script_id=script_id,
                            beat_id=beat_id,
                            scene_description_id=scene_description_id,
                            segment_number=segment_number
                        )
                        
                        db.add(db_segment)
                        db.flush()  # Get the ID without committing
                        created_segment_count += 1
                        
                        # Store the ID mapping if frontend ID was provided
                        if frontend_segment_id:
                            segment_id_map[frontend_segment_id] = str(db_segment.id)
                        
                        # Process all components in the new segment
                        if 'components' in segment_data:
                            for comp_data in segment_data['components']:
                                # comp_data = comp_data.model_dump()
                                # Get the frontend ID for mapping
                                frontend_component_id = comp_data.get('frontendId')
                                
                                # Create the component
                                component_type = comp_data.get('component_type')
                                position = comp_data.get('position')
                                content = comp_data.get('content')
                                character_name = comp_data.get('character_name')
                                parenthetical = comp_data.get('parenthetical')
                                
                                db_component = SceneSegmentComponent(
                                    scene_segment_id=db_segment.id,
                                    component_type=component_type,
                                    position=position,
                                    content=content,
                                    character_name=character_name,
                                    parenthetical=parenthetical
                                )
                                
                                db.add(db_component)
                                db.flush()  # Get the ID without committing
                                created_component_count += 1
                                
                                # Store the ID mapping if frontend ID was provided
                                if frontend_component_id:
                                    component_id_map[frontend_component_id] = str(db_component.id)
                    
                    except Exception as segment_error:
                        logger.error(f"Error creating new segment: {str(segment_error)}")
                        logger.error(traceback.format_exc())
                        continue
            
            # 2. Process new components for existing segments (if any)
            if new_components_in_existing_segments:
                logger.info(f"Processing {len(new_components_in_existing_segments)} new components")
                for comp_data in new_components_in_existing_segments:
                    try:
                        comp_data = comp_data.model_dump()
                        # Get the frontend ID for mapping
                        frontend_component_id = comp_data.get('frontendId')
                        
                        # Extract segment_id and convert to UUID if it's a string
                        segment_id_str = comp_data.get('segment_id')
                        if not segment_id_str:
                            logger.warning(f"Missing segment_id in component data: {comp_data}")
                            continue
                        
                        try:
                            # Convert to UUID if it's a string
                            segment_id = UUID(segment_id_str) if isinstance(segment_id_str, str) else segment_id_str
                        except ValueError:
                            logger.warning(f"Invalid segment ID format: {segment_id_str}")
                            continue
                        
                        logger.info(f"Looking up segment with ID: {segment_id}")
                        
                        # Verify segment exists and belongs to this script
                        segment = db.query(SceneSegment).filter(
                            and_(
                                SceneSegment.id == segment_id,
                                SceneSegment.script_id == script_id,
                                SceneSegment.is_deleted.is_(False)
                            )
                        ).first()
                        
                        if not segment:
                            logger.warning(f"Segment not found or does not belong to script: {segment_id}")
                            continue
                        
                        # Create the component
                        component_type = comp_data.get('component_type')
                        position = comp_data.get('position')
                        content = comp_data.get('content')
                        character_name = comp_data.get('character_name')
                        parenthetical = comp_data.get('parenthetical')
                        
                        logger.info(f"Creating component: type={component_type}, content={content}")
                        
                        db_component = SceneSegmentComponent(
                            scene_segment_id=segment_id,
                            component_type=component_type,
                            position=position,
                            content=content,
                            character_name=character_name,
                            parenthetical=parenthetical
                        )
                        
                        db.add(db_component)
                        db.flush()  # Get the ID without committing
                        created_component_count += 1
                        
                        # Store the ID mapping if frontend ID was provided
                        if frontend_component_id:
                            component_id_map[frontend_component_id] = str(db_component.id)
                        
                    except Exception as comp_error:
                        logger.error(f"Error creating new component: {str(comp_error)}")
                        logger.error(traceback.format_exc())
                        continue
            
            # 3. Process component updates by segment (if any)
            if changed_segments:
                for segment_id_str, components in changed_segments.items():
                    # Skip if no components to update
                    if not components:
                        continue
                        
                    try:
                        segment_id = UUID(segment_id_str)
                    except ValueError:
                        logger.warning(f"Invalid segment ID format: {segment_id_str}")
                        continue
                        
                    # Verify segment belongs to this script
                    segment = db.query(SceneSegment).filter(
                        and_(
                            SceneSegment.id == segment_id,
                            SceneSegment.script_id == script_id,
                            SceneSegment.is_deleted.is_(False)
                        )
                    ).first()
                    
                    if not segment:
                        logger.warning(f"Segment not found or does not belong to script: {segment_id}")
                        continue
                    
                    # Process each component change
                    for comp in components:
                        try:
                            # Access fields directly
                            component_id = comp["id"] if isinstance(comp, dict) else comp.id
                            component_type = comp["component_type"] if isinstance(comp, dict) else comp.component_type
                            
                            # Convert component_id to UUID if it's a string
                            try:
                                component_id = UUID(component_id) if isinstance(component_id, str) else component_id
                            except ValueError:
                                logger.warning(f"Invalid component ID format: {component_id}")
                                continue
                            
                            # Find the component
                            db_component = db.query(SceneSegmentComponent).filter(
                                and_(
                                    SceneSegmentComponent.id == component_id,
                                    SceneSegmentComponent.scene_segment_id == segment_id,
                                    SceneSegmentComponent.is_deleted.is_(False)
                                )
                            ).first()
                            
                            if not db_component:
                                logger.warning(f"Component not found: {component_id}")
                                continue
                            
                            # Special handling for PARENTHETICAL component type from frontend
                            if component_type == "PARENTHETICAL":
                                # Just update the parenthetical field
                                content = comp["content"] if isinstance(comp, dict) else comp.content
                                db_component.parenthetical = content
                                updated_count += 1
                                continue
                            
                            # Normal field updates based on component type
                            if component_type in ["HEADING", "ACTION", "DIALOGUE", "CHARACTER", "TRANSITION"]:
                                # Update component type if different
                                if db_component.component_type.value != component_type:
                                    db_component.component_type = component_type
                                
                                # Update position if provided
                                position = comp["position"] if isinstance(comp, dict) else comp.position
                                if position is not None:
                                    db_component.position = position
                                    
                                # Update content if provided
                                content = comp["content"] if isinstance(comp, dict) else comp.content
                                if content is not None:
                                    db_component.content = content
                                    
                                # Update character_name for DIALOGUE or CHARACTER types
                                if component_type in ["DIALOGUE", "CHARACTER"]:
                                    character_name = comp.get("character_name") if isinstance(comp, dict) else getattr(comp, "character_name", None)
                                    if character_name is not None:
                                        db_component.character_name = character_name
                                
                                # Update parenthetical for DIALOGUE type
                                if component_type == "DIALOGUE":
                                    parenthetical = comp.get("parenthetical") if isinstance(comp, dict) else getattr(comp, "parenthetical", None)
                                    if parenthetical is not None:
                                        db_component.parenthetical = parenthetical
                            
                            updated_count += 1
                            
                        except Exception as comp_error:
                            logger.error(f"Error updating component: {str(comp_error)}")
                            logger.error(traceback.format_exc())
                            continue
            
            # 4. Process component deletions (if any)
            if deleted_elements:
                for component_id_str in deleted_elements:
                    try:
                        component_id = UUID(component_id_str)
                    except ValueError:
                        logger.warning(f"Invalid component ID format: {component_id_str}")
                        continue
                        
                    # Find the component and verify it belongs to this script
                    component = db.query(SceneSegmentComponent).join(
                        SceneSegment, SceneSegmentComponent.scene_segment_id == SceneSegment.id
                    ).filter(
                        and_(
                            SceneSegmentComponent.id == component_id,
                            SceneSegment.script_id == script_id,
                            SceneSegmentComponent.is_deleted.is_(False)
                        )
                    ).first()
                    
                    if not component:
                        logger.warning(f"Component not found or does not belong to script: {component_id}")
                        continue
                    
                    # Soft delete the component
                    component.soft_delete()
                    deleted_component_count += 1

            # 5. Process segment deletions (if any)
            if deleted_segments:
                for segment_id_str in deleted_segments:
                    try:
                        segment_id = UUID(segment_id_str)
                    except ValueError:
                        logger.warning(f"Invalid segment ID format: {segment_id_str}")
                        continue
                    
                    # Find the segment and verify it belongs to this script
                    segment = db.query(SceneSegment).filter(
                        and_(
                            SceneSegment.id == segment_id,
                            SceneSegment.script_id == script_id,
                            SceneSegment.is_deleted.is_(False)
                        )
                    ).first()
                    
                    if not segment:
                        logger.warning(f"Segment not found or does not belong to script: {segment_id}")
                        continue
                    
                    # Soft delete the segment
                    segment.soft_delete()
                    
                    # Also soft delete all components in the segment
                    components = db.query(SceneSegmentComponent).filter(
                        and_(
                            SceneSegmentComponent.scene_segment_id == segment_id,
                            SceneSegmentComponent.is_deleted.is_(False)
                        )
                    ).all()
                    
                    for component in components:
                        component.soft_delete()
                        deleted_component_count += 1
                    
                    deleted_segment_count += 1
            
            # Commit all changes in a single transaction
            db.commit()
            
            # Prepare and return response with ID mappings
            return {
                "success": True,
                "message": "Script changes applied successfully",
                "updated_components": updated_count,
                "deleted_components": deleted_component_count,
                "deleted_segments": deleted_segment_count,
                "created_segments": created_segment_count,
                "created_components": created_component_count,
                "idMappings": {
                    "segments": segment_id_map,
                    "components": component_id_map
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying script changes: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to apply script changes: {str(e)}"
            )