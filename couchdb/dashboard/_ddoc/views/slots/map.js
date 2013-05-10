function(doc) {
  if (doc.type == "slot-config") {
    var projs = [];
    for(var idx in doc.projects) {
      projs.push({name: doc.projects[idx].name,
                  version: doc.projects[idx].version});
    }
    emit([doc.date, doc.slot],
         {"description": doc.description,
    	  "build_id": doc.build_id,
          "platforms": doc.platforms,
          "projects": projs})
  }
}
