function(doc) {
  if (doc.type == "slot-config") {
    emit([doc.date, doc.slot],
         {"build_id": doc.build_id,
          "platforms": doc.platforms,
          "projects": doc.projects})
  }
}
