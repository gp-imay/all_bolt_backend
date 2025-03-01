# app/services/scene_segment_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging

from models.scene_segments import SceneSegment, SceneSegmentComponent, ComponentType
from models.script import Script
from models.beats import Beat
from models.scenes import SceneDescription
from schemas.scene_segment import SceneSegmentCreate, SceneSegmentUpdate, ComponentCreate, ComponentUpdate

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