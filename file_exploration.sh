NAME="product"
echo "# Product Refactoring" > ${NAME}_refs.md

printf "\n## All\n" >> ${NAME}_refs.md

rg -n --heading --color=never \
--glob '*.py' \
--glob '!app/models/**' \
--glob '!app/services/**' \
--glob '!app/schemas/**' \
--glob '!app/routes/**' \
--glob '!tests/**' \
'\bProduct\b' \
  | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
  | sed 's/`/\\`/g' \
  | sed 's/_/\\_/g' \
  >> ${NAME}_refs.md

printf "\n## Models\n" >> ${NAME}_refs.md

rg -n --heading --color=never '\bProduct\b' app/models \
  | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
  | sed 's/`/\\`/g' \
  | sed 's/_/\\_/g' \
  >> ${NAME}_refs.md

echo "\n## Schemas\n" >> ${NAME}_refs.md
rg -n --heading '\bProduct\b' app/schemas \
    | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
    | sed 's/`/\\`/g' \
    | sed 's/_/\\_/g' \
    >> ${NAME}_refs.md

echo -e "\n## Routes\n" >> ${NAME}_refs.md
rg -n --heading '\bProduct\b' app/routes \
    | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
    | sed 's/`/\\`/g' \
    | sed 's/_/\\_/g' \
    >> ${NAME}_refs.md

echo -e "\n## Services\n" >> ${NAME}_refs.md
rg -n --heading '\bProduct\b' app/services \
    | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
    | sed 's/`/\\`/g' \
    | sed 's/_/\\_/g' \
    >> ${NAME}_refs.md

echo -e "\n## Tests\n" >> ${NAME}_refs.md
rg -n --heading '\bProduct\b' tests \
    | sed '/^[^0-9].*\.py$/s/^/- [ ] /' \
    | sed 's/`/\\`/g' \
    | sed 's/_/\\_/g' \
    >> ${NAME}_refs.md