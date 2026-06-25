"""
API Routes for AJAX requests
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from .auth import token_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'timestamp': datetime.utcnow().isoformat()}), 200


@api_bp.route('/search', methods=['GET'])
@token_required
def search():
    """Global search endpoint"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if len(query) < 2:
        return jsonify({'results': [], 'message': 'Query too short'}), 400
    
    try:
        if request.user_role == 'admin':
            from backend.models import User, Company, Student
            results = []
            
            if search_type in ['all', 'student']:
                students = Student.query.join(User).filter(
                    (User.name.ilike(f'%{query}%')) |
                    (User.email.ilike(f'%{query}%'))
                ).limit(10).all()
                results.extend([{'type': 'student', **s.to_dict()} for s in students])
            
            if search_type in ['all', 'company']:
                companies = Company.query.join(User).filter(
                    (Company.company_name.ilike(f'%{query}%')) |
                    (User.email.ilike(f'%{query}%'))
                ).limit(10).all()
                results.extend([{'type': 'company', **c.to_dict()} for c in companies])
            
            return jsonify({'results': results}), 200
        
        elif request.user_role == 'student':
            from backend.models import PlacementDrive, Company
            
            drives = PlacementDrive.query.join(Company).filter(
                PlacementDrive.status == 'approved'
            ).filter(
                (PlacementDrive.job_title.ilike(f'%{query}%')) |
                (Company.company_name.ilike(f'%{query}%')) |
                (PlacementDrive.location.ilike(f'%{query}%'))
            ).limit(10).all()
            
            results = [d.to_dict() for d in drives]
            return jsonify({'results': results}), 200
        
        elif request.user_role == 'company':
            from backend.models import User, Student
            
            students = Student.query.join(User).filter(
                (User.name.ilike(f'%{query}%')) |
                (User.email.ilike(f'%{query}%')) |
                (Student.branch.ilike(f'%{query}%'))
            ).limit(10).all()
            
            results = [s.to_dict() for s in students]
            return jsonify({'results': results}), 200
        
        return jsonify({'results': []}), 200
    
    except Exception as e:
        return jsonify({'message': str(e)}), 500